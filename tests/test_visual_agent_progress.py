"""Regressions for live click loops; screenshots may change only by caret blink."""
import json
from PIL import Image,ImageDraw
from app.agent.visual.runtime import VisualFrame,run_visual_task,image_change
from app.agent.visual.windows_driver import FrameToken
from tools.run_visual_agent import LabTrace

def action(kind,**extra):
    value=dict(kind=kind,x=None,y=None,width=None,height=None,text=None,key=None,direction=None,amount=None,reason='Synthetic action')
    value.update(extra);return value

class Driver:
    def __init__(self):self.image=Image.new('RGB',(680,400),'white');self.calls=[];self.captures=0
    def capture(self):
        self.captures+=1
        image=self.image.copy()
        # Tiny pixel changes defeat an exact screenshot hash but not the guard.
        image.putpixel((self.captures%100,0),(0,0,0))
        return VisualFrame(image,None)
    def is_fresh(self,*args):return True
    def perform(self,frame,action):self.calls.append(action)

class Reasoner:
    def __init__(self,actions):self.actions=iter(actions);self.requests=[]
    def reason(self,request):
        self.requests.append(request)
        return dict(version='visual-1',task_id=request['task_id'],turn=request['turn'],action=next(self.actions))

def test_caret_blink_and_small_coordinate_drift_do_not_allow_click_loop():
    driver=Driver();model=Reasoner([action('click',x=x,y=60) for x in (100,103,98,101)])
    assert run_visual_task(driver,model,'Goal',execute=True,max_steps=8)=='review'
    assert len(driver.calls)==1
    assert len(model.requests)==3
    assert any('BLOCKED' in item['status'] for item in model.requests[-1]['feedback'])

def test_wandering_clicks_without_effect_stop_before_fourth_model_call():
    driver=Driver();model=Reasoner([action('click',x=x,y=60) for x in (20,100,180,260)])
    assert run_visual_task(driver,model,'Goal',execute=True,max_steps=8)=='review'
    assert len(driver.calls)==3 and len(model.requests)==3

def test_model_receives_previous_click_location_and_can_switch_to_typing():
    driver=Driver();model=Reasoner([action('click',x=120,y=80),action('key',key='CTRL+A'),action('type_text',text='Top Trans'),action('done')])
    assert run_visual_task(driver,model,'Goal',execute=True,max_steps=8,verify=lambda:len(driver.calls)==3)=='verified'
    feedback=model.requests[1]['feedback']
    assert any('"x":120' in item['status'] and '"y":80' in item['status'] for item in feedback)
    assert any('No substantial image change' in item['status'] for item in feedback)
    assert [item['kind'] for item in driver.calls]==['click','key','type_text']

def test_small_blink_is_separated_from_visible_field_change():
    before=Image.new('RGB',(680,400),'white');after=before.copy()
    ImageDraw.Draw(after).rectangle((100,100,101,115),fill='black')
    assert image_change(before,after)<.0005
    ImageDraw.Draw(after).rectangle((100,100,200,120),fill='black')
    assert image_change(before,after)>.0005

def test_visible_change_resets_click_guard_and_does_not_claim_completion():
    driver=Driver()
    def perform(frame,a):
        driver.calls.append(a)
        color='black' if len(driver.calls)%2 else 'white'
        ImageDraw.Draw(driver.image).rectangle((0,30,400,100),fill=color)
    driver.perform=perform
    model=Reasoner([action('click',x=120,y=80)]*4)
    assert run_visual_task(driver,model,'Goal',execute=True,max_steps=4)=='review'
    # Exact repeated image/action pairs are separately bounded; changed images
    # do not count toward the no-effect guard or prove goal completion.
    assert len(driver.calls)>=2

def test_trace_keeps_exact_image_and_requested_point_local(tmp_path):
    frame=VisualFrame(Image.new('RGB',(100,100),'white'),FrameToken(7,8,(-200,300,200,700),(100,100,300,300)))
    trace=LabTrace(tmp_path)
    trace(0,frame,action('click',x=10,y=20))
    record=json.loads((trace.path/'turn-00.json').read_text(encoding='utf-8'))
    assert record['requested_desktop_point']==[-80,440]
    assert record['proposed_action']['x']==10
    assert Image.open(trace.path/'turn-00.png').size==(100,100)
    assert set(record)=={'turn','image_size','proposed_action','window_box','view_box','requested_desktop_point'}

def test_toggling_visual_states_with_jittered_clicks_cannot_bypass_loop_guard():
    driver=Driver()
    def perform(frame,a):
        driver.calls.append(a)
        color='black' if len(driver.calls)%2 else 'white'
        ImageDraw.Draw(driver.image).rectangle((0,30,400,100),fill=color)
    driver.perform=perform
    model=Reasoner([action('click',x=x,y=80) for x in (120,122,119,121)])
    assert run_visual_task(driver,model,'Goal',execute=True,max_steps=4)=='review'
    assert len(driver.calls)==2
    assert any('visually equivalent' in item['status'] for item in model.requests[-1]['feedback'])


def test_stale_typing_attempt_does_not_block_a_fresh_retry_of_same_action(capsys):
    driver = Driver()
    driver.capture = lambda: VisualFrame(driver.image.copy(), None)
    checks = iter([False, True])
    driver.is_fresh = lambda *args: next(checks)
    typing = action("type_text", text="Top")
    model = Reasoner([typing, typing, action("done")])

    assert run_visual_task(
        driver, model, "Find the customer", execute=True, verify=lambda: driver.calls == [typing],
    ) == "verified"
    assert "VISUAL_ACTION_BLOCKED=stale_frame" in capsys.readouterr().out
    assert "No input was attempted" in model.requests[1]["feedback"][-1]["status"]


def test_crop_feedback_explains_how_to_return_to_full_window():
    driver = Driver()
    model = Reasoner([
        action("inspect", x=10, y=10, width=200, height=200),
        action("inspect"),
        action("done"),
    ])
    assert run_visual_task(driver, model, "Goal", execute=True, verify=lambda: True) == "verified"
    assert "null bounds" in model.requests[1]["feedback"][-1]["status"]
    assert "Full-window screenshot" in model.requests[2]["feedback"][-1]["status"]


def test_windows_capture_uses_client_bounds_for_image_and_click_mapping(monkeypatch):
    from contextlib import nullcontext
    from types import SimpleNamespace

    from app.agent.visual import windows_driver

    driver = windows_driver.WindowsVisualDriver.__new__(windows_driver.WindowsVisualDriver)
    driver.hwnd, driver.pid, driver.view = 7, 8, None
    driver._check = lambda: None

    def client_rect(hwnd, pointer):
        assert hwnd == 7
        pointer._obj.right, pointer._obj.bottom = 920, 600
        return True

    def client_to_screen(hwnd, pointer):
        assert hwnd == 7
        pointer._obj.x, pointer._obj.y = 134, 164
        return True

    driver.user32 = SimpleNamespace(GetClientRect=client_rect, ClientToScreen=client_to_screen)
    monkeypatch.setattr(windows_driver, "physical_coordinates", nullcontext)

    def grab(*, bbox, all_screens):
        assert bbox == (134, 164, 1054, 764)
        assert all_screens is True
        return Image.new("RGB", (920, 600))

    monkeypatch.setattr(windows_driver.ImageGrab, "grab", grab)
    frame = driver.capture()
    assert frame.token.window_box == (134, 164, 1054, 764)
    assert windows_driver.model_to_window(frame, 100, 170) == (100, 170)


def test_latest_form_observation_is_sent_on_each_turn():
    driver = Driver()
    model = Reasoner([action("click", x=100, y=80), action("done")])
    assert run_visual_task(
        driver, model, "Goal", execute=True, verify=lambda: True,
        observe=lambda: "selected" if driver.calls else "not selected",
    ) == "verified"
    assert model.requests[0]["feedback"][-1] == {"action": "observe", "status": "not selected"}
    assert model.requests[1]["feedback"][-1] == {"action": "observe", "status": "selected"}
