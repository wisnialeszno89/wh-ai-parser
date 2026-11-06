import base64,io,json
from PIL import Image
import pytest
from app.agent.visual.contract import validate_action,validate_request,validate_response
from app.agent.visual.runtime import VisualFrame,run_visual_task
from app.agent.visual.client import VisualReasoner
from app.agent.visual.windows_driver import FrameToken,model_to_window,literal_keys
from tools.visual_agent_lab import LabState
from tools.run_visual_agent import lab_verifier


def action(kind,**extra):
    fields=dict(kind=kind,x=None,y=None,width=None,height=None,text=None,key=None,direction=None,amount=None,reason='Synthetic fixture')
    fields.update(extra)
    return fields

class Driver:
    def __init__(self):self.image=Image.new('RGB',(200,100),'white');self.actions=[];self.value='ATop Trans';self.selected=False;self.checked=False;self.submitted=False
    def capture(self):return VisualFrame(self.image.copy(),None)
    def is_fresh(self,*a):return True
    def perform(self,frame,a):
        self.actions.append(a['kind'])
        if a['kind']=='key':self.selected=True
        if a['kind']=='type_text':self.value=a['text'] if self.selected else self.value+a['text']
        if a['kind']=='click' and a['x']==50:self.checked=True
        if a['kind']=='click' and a['x']==100:self.submitted=True
        self.image.putpixel((len(self.actions),0),(len(self.actions),0,0))

class FixtureReasoner:
    def __init__(self,actions):self.actions=iter(actions);self.requests=[]
    def reason(self,request):
        self.requests.append(request)
        # The actual PNG is present, not only a description or file path.
        image=Image.open(io.BytesIO(base64.b64decode(request['screen']['image_data_url'][22:])))
        assert image.size==(request['screen']['width'],request['screen']['height'])
        return dict(version='visual-1',task_id=request['task_id'],turn=request['turn'],action=next(self.actions))


def test_image_loop_corrects_typo_then_checks_independent_result():
    driver=Driver();model=FixtureReasoner([action('key',key='CTRL+A'),action('type_text',text='Top Trans'),action('click',x=50,y=50),action('click',x=100,y=50),action('done')])
    verified=lambda:driver.value=='Top Trans' and driver.checked and driver.submitted
    assert run_visual_task(driver,model,'Correct client and install',execute=True,verify=verified)=='verified'
    assert driver.value=='Top Trans' and len(model.requests)==5
    assert model.requests[0]['screen']['image_data_url']!=model.requests[1]['screen']['image_data_url']


def test_done_without_local_verifier_does_not_claim_success():
    assert run_visual_task(Driver(),FixtureReasoner([action('done')]),'Goal',execute=True)=='review'


def test_done_rejection_returns_feedback_and_new_screenshot():
    driver=Driver();model=FixtureReasoner([action('done'),action('key',key='CTRL+A'),action('type_text',text='Top Trans'),action('done')])
    assert run_visual_task(driver,model,'Correct text',execute=True,verify=lambda:driver.value=='Top Trans')=='verified'
    assert 'rejected' in model.requests[1]['feedback'][0]['status']


def test_think_sends_image_but_does_not_execute():
    driver=Driver()
    assert run_visual_task(driver,FixtureReasoner([action('click',x=10,y=10)]),'Goal')=='proposed'
    assert driver.actions==[]


def test_stale_screen_never_dispatches_click():
    driver=Driver();driver.is_fresh=lambda *a:False
    assert run_visual_task(driver,FixtureReasoner([action('click',x=10,y=10)]),'Goal',execute=True,max_steps=1)=='review'
    assert not driver.actions


def test_identical_actions_on_unchanged_image_are_blocked():
    driver=Driver();driver.perform=lambda frame,a:driver.actions.append(a['kind'])
    model=FixtureReasoner([action('click',x=10,y=10)]*3)
    assert run_visual_task(driver,model,'Goal',execute=True,max_steps=3)=='review'
    assert driver.actions==['click']


@pytest.mark.parametrize('invalid',[action('click',x=200,y=0),action('click',x=True,y=0),action('key',key='CTRL+S'),action('type_text',text='x\n'),action('done',text='hidden')])
def test_invalid_model_actions_are_rejected(invalid):
    with pytest.raises(ValueError):validate_action(invalid,200,100)


def test_response_is_bound_to_task_and_screenshot_turn():
    frame=VisualFrame(Image.new('RGB',(20,20)),None)
    request=dict(version='visual-1',task_id='t',turn=1,goal='Goal',screen=frame.screen(),feedback=[])
    validate_request(request)
    with pytest.raises(ValueError,match='revision'):
        validate_response(dict(version='visual-1',task_id='t',turn=0,action=action('done')),request)


def test_zoom_coordinates_map_to_current_view_not_full_desktop():
    frame=VisualFrame(Image.new('RGB',(100,100)),FrameToken(7,8,(20,30,420,430),(100,100,300,300)))
    assert model_to_window(frame,10,20)==(120,140)


def test_text_is_literal_and_not_keyboard_macro():
    assert literal_keys('A+B^{ENTER}')=='A{+}B{^}{{}ENTER{}}'


def test_lab_proof_requires_same_session_and_submitted_actual_values(tmp_path):
    path=tmp_path/'lab.json';state=LabState();state.save(path)
    verify=lab_verifier(path,state.nonce,__import__('os').getpid())
    assert verify() is False
    state.text='Top Trans';state.checked=True;state.save(path);assert verify() is False
    state.submitted=True;state.save(path);assert verify() is True
    wrong=lab_verifier(path,'other-session',__import__('os').getpid());assert wrong() is False


def test_client_sends_png_and_auth_without_exposing_native_handles():
    captured=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,limit):
            req=json.loads(captured[0].data)
            return json.dumps(dict(version='visual-1',task_id=req['task_id'],turn=req['turn'],action=action('inspect'))).encode()
    def opener(request,timeout):captured.append(request);return Response()
    request=dict(version='visual-1',task_id='transport',turn=0,goal='Goal',screen=VisualFrame(Image.new('RGB',(20,20)),object()).screen(),feedback=[])
    response=VisualReasoner('https://example.com/api/agent/visual-task','test-secret',opener,access_url='').reason(request)
    assert response['action']['kind']=='inspect'
    body=json.loads(captured[0].data)
    assert body['screen']['image_data_url'].startswith('data:image/png;base64,')
    assert 'hwnd' not in json.dumps(body)


def test_partial_typing_failure_is_reobserved_before_model_correction():
    driver=Driver()
    original=driver.perform
    first=[True]
    def perform(frame,a):
        if a['kind']=='type_text' and first[0]:
            first[0]=False;driver.value='ATop';driver.image.putpixel((0,0),(10,10,10))
            raise RuntimeError('partial_input')
        original(frame,a)
    driver.perform=perform
    model=FixtureReasoner([action('type_text',text='Top Trans'),action('key',key='CTRL+A'),action('type_text',text='Top Trans'),action('done')])
    assert run_visual_task(driver,model,'Correct text',execute=True,verify=lambda:driver.value=='Top Trans')=='verified'
    assert 'MAY have partially executed' in model.requests[1]['feedback'][0]['status']


def test_protected_preview_bootstraps_without_application_secret():
    calls=[]
    request=dict(version='visual-1',task_id='protected-test',turn=0,goal='Goal',screen=VisualFrame(Image.new('RGB',(20,20)),None).screen(),feedback=[])
    class Response:
        def __init__(self,data):self.data=data
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,limit):return self.data
    def opener(req,timeout):
        calls.append(req)
        if req.get_method()=='GET':return Response(b'ok')
        return Response(json.dumps(dict(version='visual-1',task_id='protected-test',turn=0,action=action('inspect'))).encode())
    client=VisualReasoner('https://example.com/api/agent/visual-task','test-secret',opener,access_url='https://example.com/?_vercel_share=synthetic-share')
    client.reason(request);client.reason(request)
    assert [r.get_method() for r in calls]==['GET','POST','POST']
    assert not any(k.lower()=='x-navimind-agent-secret' for k in calls[0].headers)
    assert calls[1].get_header('X-navimind-agent-secret')=='test-secret'


def test_protected_preview_rejects_foreign_access_link():
    with pytest.raises(ValueError,match='same_origin'):
        VisualReasoner('https://example.com/api/agent/visual-task','test-secret',access_url='https://other.example/?_vercel_share=synthetic-share')


def test_application_secret_cannot_follow_redirect_to_foreign_origin():
    from app.agent.visual.client import SameOriginRedirects
    from urllib.request import Request
    from urllib.error import HTTPError
    req=Request('https://example.com/api/agent/visual-task',data=b'{}',headers={'x-navimind-agent-secret':'synthetic-secret'},method='POST')
    with pytest.raises(HTTPError,match='cross_origin'):
        SameOriginRedirects(req.full_url).redirect_request(req,None,302,'Found',{},'https://login.other.example/')


@pytest.mark.parametrize('status,body,expected',[
    (400,b'{"error":"INVALID_VISUAL_TASK"}','ready'),
    (401,b'{"error":"UNAUTHORIZED"}','application_secret_rejected'),
    (401,b'<html>Authentication required</html>','preview_access_rejected'),
    (503,b'{"error":"VISUAL_NOT_ENABLED"}','visual_not_enabled'),
])
def test_connection_probe_distinguishes_auth_without_image_or_model(status,body,expected):
    from urllib.error import HTTPError
    calls=[]
    def opener(req,timeout):
        calls.append(req)
        raise HTTPError(req.full_url,status,'Synthetic',{},io.BytesIO(body))
    result=VisualReasoner('https://example.com/api/agent/visual-task','test-secret',opener,access_url='').probe()
    assert result==expected
    assert len(calls)==1 and calls[0].data==b'{}'
    assert b'image' not in calls[0].data
