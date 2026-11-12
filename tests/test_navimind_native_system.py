import copy,json
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
import pytest
from tools.navimind_native import NativeController,validate_native
from tools.navimind_system import DesktopWithDiagnostics,collect_facts
from app.agent.visual.runtime import VisualFrame
from tools.run_navimind_desktop_bridge import TableExecutor

class Driver:
    def __init__(self,path):self.path=path;self.image=Image.new('RGB',(100,80),'white');self.fresh=True;self.calls=[];self.window=SimpleNamespace(window_text=lambda:path.name+' - Paint')
    def focus(self):pass
    def capture(self):return VisualFrame(self.image.copy(),('owned-window',100,80))
    def is_fresh(self,frame,action):return self.fresh
    def perform(self,frame,action):
        self.calls.append(action)
        if action['kind']=='key' and action['key']=='CTRL+S':self.image.save(self.path)
        else:ImageDraw.Draw(self.image).rectangle((10,10,40,40),fill='black')

def setup(tmp_path):
    path=tmp_path/'owned.png';Image.new('RGB',(100,80),'white').save(path);driver=Driver(path);agent=NativeController(driver,path);agent.start({});return agent,driver

def job(agent,task,id='native-job-12345678'):return dict(id=id,task=task,expectedRevision=agent.snapshot['revision'],session=agent.session)

def test_actions_are_image_bounded_and_keys_are_explicit():
    validate_native(dict(kind='native_drag',points=[dict(x=0,y=0),dict(x=99,y=79)]),100,80)
    for task in [dict(kind='native_click',x=100,y=0),dict(kind='native_key',key='WIN+R'),dict(kind='native_text',text='\0'),dict(kind='native_drag',points=[dict(x=0,y=0)]),dict(kind='native_click',x=True,y=2),dict(kind='shell',command='anything')]:
        with pytest.raises(ValueError):validate_native(task,100,80)

def test_stale_frame_never_dispatches_input(tmp_path):
    a,d=setup(tmp_path);d.fresh=False;r=a.execute(job(a,dict(kind='native_click',x=12,y=12)))
    assert r['code']=='STALE_NATIVE_FRAME' and d.calls==[]

def test_step_recovery_and_finish_do_not_replay_input(tmp_path):
    a,d=setup(tmp_path);body=job(a,dict(kind='native_drag',points=[dict(x=10,y=10),dict(x=40,y=40)]));r=a.execute(body)
    assert r['status']=='verified' and r['native']['scope']=='owned_paint_window';assert a.execute(body)==r;assert len(d.calls)==1
    finish=job(a,dict(kind='native_finish'),id='native-finish-123456');r=a.execute(finish)
    assert r['status']=='verified' and r['native_result']['saved_pixels_changed'] and not r['native_result']['goal_verified']
    assert a.execute(finish)==r and len(d.calls)==2
    assert a.execute({**finish,'task':dict(kind='native_key',key='ESC')})['status']=='review'

def test_different_document_stops_without_input(tmp_path):
    a,d=setup(tmp_path);d.window.window_text=lambda:'different document';r=a.execute(job(a,dict(kind='native_click',x=12,y=12)))
    assert r['status']=='review' and not d.calls

def test_diagnostics_are_saved_without_touching_active_table(tmp_path):
    tables=TableExecutor(tmp_path,object());facts={'schema':1,'memory':None,'os':{'system':'Windows'},'system_disk':{'total_bytes':100,'free_bytes':50}}
    a=DesktopWithDiagnostics(tables,lambda:copy.deepcopy(facts));body=dict(id='diagnostic-job-12345',task=dict(kind='inspect_computer',folder='Diagnostyka',file_name='raport.json'),expectedRevision=None)
    r=a.execute(body);assert r['status']=='verified' and r['system_report']==facts and tables.active is None
    assert json.loads(Path(r['file']).read_text())==facts;assert a.execute(body)==r
    r2=a.execute({**body,'id':'another-report-12345'});assert Path(r2['file']).name=='raport-2.json' and Path(r['file']).exists()
    with pytest.raises(ValueError):a.execute({**body,'task':{**body['task'],'folder':'../outside'}})

def test_readonly_facts_do_not_collect_accounts_network_or_process_names():
    facts=collect_facts();assert facts['cpu']['logical_processors']>0 and facts['system_disk']['free_bytes']<=facts['system_disk']['total_bytes']
    assert not {'username','hostname','network','processes','environment','serial','credentials'}&set(facts)


def test_native_drag_releases_at_last_owned_point_even_when_focus_changes(monkeypatch):
    import contextlib,sys
    from app.agent.visual import windows_driver as module
    from app.agent.visual.windows_driver import WindowsVisualDriver,FrameToken
    calls=[]
    mouse=SimpleNamespace(press=lambda **kw:calls.append(('press',kw)),move=lambda **kw:calls.append(('move',kw)),release=lambda **kw:calls.append(('release',kw)))
    monkeypatch.setitem(sys.modules,'pywinauto',SimpleNamespace(mouse=mouse))
    monkeypatch.setitem(sys.modules,'pywinauto.keyboard',SimpleNamespace(send_keys=lambda *a,**k:None))
    monkeypatch.setattr(module,'physical_coordinates',contextlib.nullcontext)
    d=WindowsVisualDriver.__new__(WindowsVisualDriver);checks=[]
    def check():
        checks.append(True)
        if len(checks)==3:raise RuntimeError('foreground_changed')
    d._check=check;d._owned_point=lambda x,y:None
    frame=VisualFrame(Image.new('RGB',(100,80)),FrameToken(1,2,(10,20,110,100),(0,0,100,80)))
    with pytest.raises(RuntimeError):d.perform(frame,dict(kind='drag',points=[dict(x=10,y=10),dict(x=50,y=50)]))
    assert calls==[('press',{'coords':(20,30)}),('release',{'coords':(20,30)})]


def test_window_occlusion_guard_blocks_unrelated_overlay(monkeypatch):
    import contextlib,sys
    from app.agent.visual import windows_driver as module
    from app.agent.visual.windows_driver import WindowsVisualDriver
    d=WindowsVisualDriver.__new__(WindowsVisualDriver);d.hwnd=10;d.pid=1;d._check=lambda:None;d._client_box=lambda:(0,0,100,80)
    monkeypatch.setattr(module,'physical_coordinates',contextlib.nullcontext)
    gui=SimpleNamespace(GetWindow=lambda hwnd,_:20 if hwnd==10 else 0,IsWindowVisible=lambda _:True,IsIconic=lambda _:False,GetWindowRect=lambda _:(20,20,50,50))
    monkeypatch.setitem(sys.modules,'win32gui',gui);monkeypatch.setitem(sys.modules,'win32process',SimpleNamespace(GetWindowThreadProcessId=lambda _:(1,2)))
    with pytest.raises(RuntimeError):d.assert_unobscured()
    monkeypatch.setitem(sys.modules,'win32process',SimpleNamespace(GetWindowThreadProcessId=lambda _:(1,1)))
    d.assert_unobscured()


def test_new_command_invalidates_inflight_old_session_without_dispatch(tmp_path):
    a,d=setup(tmp_path);old=job(a,dict(kind='native_click',x=12,y=12));a.start({})
    result=a.execute(old);assert result['code']=='SESSION_CHANGED' and not d.calls
