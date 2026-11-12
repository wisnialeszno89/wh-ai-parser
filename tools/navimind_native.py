"""Screenshot-based application controller; first supported scope is a new owned Paint file."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
from PIL import Image

KEYS={'CTRL+S','CTRL+Z','CTRL+Y','CTRL+A','BACKSPACE','DELETE','ESC','ENTER','TAB','SHIFT+TAB','HOME','END','LEFT','RIGHT','UP','DOWN'}


def validate_native(task,width,height):
    if not isinstance(task,dict):raise ValueError('Nieprawidlowy krok aplikacji.')
    kind=task.get('kind')
    fields={'native_target':{'kind','ref'},'native_click':{'kind','x','y'},'native_drag':{'kind','points'},'native_text':{'kind','text'},'native_key':{'kind','key'},'native_scroll':{'kind','direction','amount'},'native_wait':{'kind','amount'},'native_finish':{'kind'}}
    if not isinstance(kind,str) or kind not in fields or set(task)!=fields[kind]:raise ValueError('Nieobslugiwany krok aplikacji.')
    def point(p):
        if not isinstance(p,dict) or set(p)!={'x','y'} or type(p['x']) is not int or type(p['y']) is not int or not 0<=p['x']<width or not 0<=p['y']<height:raise ValueError('Punkt poza aktualnym obrazem okna.')
    if kind=='native_target' and (not isinstance(task['ref'],str) or not re.fullmatch(r'e[0-9a-f]{16}',task['ref'])):raise ValueError('Nieprawidlowy element okna.')
    if kind=='native_click':point({'x':task['x'],'y':task['y']})
    if kind=='native_drag':
        if not isinstance(task['points'],list) or not 2<=len(task['points'])<=24:raise ValueError('Przeciagniecie wymaga 2–24 punktow.')
        for p in task['points']:point(p)
    if kind=='native_text' and (not isinstance(task['text'],str) or not 1<=len(task['text'])<=1000 or '\x00' in task['text']):raise ValueError('Nieprawidlowy tekst.')
    if kind=='native_key' and (not isinstance(task['key'],str) or task['key'] not in KEYS):raise ValueError('Nieobslugiwany skrot klawiatury.')
    if kind in {'native_scroll','native_wait'} and (type(task['amount']) is not int or not 1<=task['amount']<=(3 if kind=='native_scroll' else 2)):raise ValueError('Nieprawidlowa wielkosc kroku.')
    if kind=='native_scroll' and task['direction'] not in {'up','down'}:raise ValueError('Nieprawidlowy kierunek.')
    return task


def file_pixels(path):
    with Image.open(path) as image:
        image.load()
        if image.format!='PNG' or image.width>2000 or image.height>1600:raise ValueError('Nieprawidlowy plik sesji Painta.')
        return hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()


class NativeController:
    def __init__(self,driver,path,results=None):
        self.driver,self.path=driver,Path(path)
        self.resolved=self.path.resolve();self.results=results if results is not None else {}
        self.frame=None;self.snapshot=None;self.baseline=None;self.lock=threading.Lock();self.started=False;self.session=None;self.targets={}
    def _check_document(self):
        if self.path.is_symlink() or self.path.resolve()!=self.resolved:raise ValueError('Plik sesji zmienil polozenie.')
        if self.path.stem.casefold() not in self.driver.window.window_text().casefold():raise ValueError('Paint otworzyl inny dokument. Wroc do pliku sesji NaviMind.')
    def _capture(self):
        self._check_document()
        if hasattr(self.driver,'assert_unobscured'):
            try:self.driver.assert_unobscured()
            except RuntimeError:raise ValueError('Okno Painta jest zasloniete albo utracilo fokus. Uaktywnij je i sprobuj ponownie.') from None
        frame=self.driver.capture()
        screen=frame.screen()
        if len(screen['image_data_url'])>2800000:raise ValueError('Obraz okna jest zbyt duzy do analizy.')
        revision=hashlib.sha256(frame.image.tobytes()+repr(frame.token).encode()).hexdigest()
        self.frame=frame;self.targets={};controls=[]
        if hasattr(self.driver,'describe_controls'):
            try:
                for target in self.driver.describe_controls(frame):
                    ref='e'+secrets.token_hex(8);self.targets[ref]=target;controls.append({'ref':ref,**target})
            except Exception:controls=[];self.targets={}
        self.snapshot={'revision':revision,'image':screen['image_data_url'],'width':frame.image.width,'height':frame.image.height,'title':self.driver.window.window_text()[:200],'scope':'owned_paint_window','controls':controls}
        return self.snapshot
    def start(self,body):
        if body!={}:raise ValueError('Nieprawidlowy poczatek zadania.')
        self._check_document();self.driver.focus()
        if hasattr(self.driver,'park_pointer'):self.driver.park_pointer()
        self.baseline=file_pixels(self.path);self.started=True;self.session=secrets.token_hex(16)
        return {**self._capture(),'session':self.session}
    def observe(self):return self._capture()
    def execute(self,body):
        if not isinstance(body,dict) or set(body)!={'id','task','expectedRevision','session'} or not isinstance(body['id'],str) or not re.fullmatch(r'[a-zA-Z0-9-]{16,80}',body['id']):raise ValueError('Nieprawidlowe zadanie aplikacji.')
        fingerprint=hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        with self.lock:
            cached=self.results.get(body['id'])
            if cached:
                return cached[1] if cached[0]==fingerprint else {'status':'review','message':'Identyfikator nalezy do innego zadania.'}
            if body['session']!=self.session:return {'status':'review','code':'SESSION_CHANGED','message':'Inne polecenie rozpoczelo nowa sesje tego okna. Starego kroku nie wykonano.'}
            if not self.snapshot or not self.started:raise ValueError('Najpierw rozpocznij zadanie w trybie Aplikacja.')
            task=validate_native(body['task'],self.snapshot['width'],self.snapshot['height'])
            if len(self.results)>=500:raise ValueError('Uruchom nowa sesje wykonawcy.')
            result={'status':'review','message':'Krok rozpoczęto. Nie ponawiaj automatycznie.'};self.results[body['id']]=(fingerprint,result)
            try:
                self._check_document();frame=self.frame;kind=task['kind']
                action={'native_target':'click','native_click':'click','native_drag':'drag','native_text':'type_text','native_key':'key','native_scroll':'scroll','native_wait':'wait','native_finish':'key'}[kind]
                args={k:v for k,v in task.items() if k!='kind'}
                if kind=='native_target':
                    if task['ref'] not in self.targets:raise ValueError('Element nie pochodzi z aktualnego widoku.')
                    target=self.targets[task['ref']];args={'x':target['x'],'y':target['y']}
                if kind=='native_finish':args={'key':'CTRL+S'}
                operation={'kind':action,**args}
                if body['expectedRevision']!=self.snapshot['revision'] or not self.driver.is_fresh(frame,operation):
                    result={'status':'review','code':'STALE_NATIVE_FRAME','message':'Okno zmienilo sie podczas planowania. Starego kroku nie wykonano.'}
                else:
                    self.driver.perform(frame,operation)
                    if kind!='native_finish' and hasattr(self.driver,'park_pointer'):self.driver.park_pointer()
                    time.sleep(.25)
                    if kind=='native_finish':
                        deadline=time.monotonic()+5
                        while time.monotonic()<deadline and file_pixels(self.path)==self.baseline:time.sleep(.2)
                        self._check_document()
                        if file_pixels(self.path)==self.baseline:raise ValueError('Nie potwierdzono zapisania nowych pikseli. Sprawdz rysunek i zapis w Paint.')
                        self.started=False
                        result={'status':'verified','file':str(self.path),'message':'Potwierdzono zapis zmienionego PNG. Sprawdz wizualnie zgodnosc rysunku z poleceniem.','native_result':{'saved_pixels_changed':True,'goal_verified':False}}
                    else:
                        snapshot=self._capture()
                        from app.agent.visual.runtime import image_change
                        change=image_change(frame.image,self.frame.image) if frame.token==self.frame.token else 1.0
                        result={'status':'verified','message':'Wykonano krok i odczytano obraz. Zmiana pikseli: '+format(change,'.5f')+'. Sprawdz semantyczny efekt; sama zmiana nie potwierdza celu.','native':snapshot}
            except Exception as exc:
                result={'status':'review','message':str(exc)[:500] if isinstance(exc,ValueError) else 'Nie potwierdzono kroku lub okno utracilo fokus. Sprawdz wybrany Paint. ('+type(exc).__name__+')'}
            self.results[body['id']]=(fingerprint,result)
            return result


class DesktopWithNative:
    def __init__(self,tables,controller):
        self.tables,self.controller=tables,controller;self.root=tables.root;self.results=tables.results;controller.results=self.results
    def __getattr__(self,name):return getattr(self.tables,name)
    def status(self):
        try:
            self.controller._check_document();title=self.controller.driver.window.window_text()[:200];available=True
        except Exception:title='';available=False
        return {**self.tables.status(),'native':{'available':available,'scope':'owned_paint_window','title':title}}
    def native_start(self,body):return self.controller.start(body)
    def native_observe(self):return self.controller.observe()
    def execute(self,body):
        if isinstance(body,dict) and isinstance(body.get('task'),dict) and str(body['task'].get('kind','')).startswith('native_'):return self.controller.execute(body)
        return self.tables.execute(body)


def start_native_paint(root):
    import sys
    root_path=str(Path(__file__).resolve().parents[1])
    if root_path not in sys.path:sys.path.insert(0,root_path)
    try:
        from .navimind_paint import PaintLauncher
    except ImportError:
        from navimind_paint import PaintLauncher
    from app.agent.visual.windows_driver import WindowsVisualDriver
    folder=Path(root)/'Rysunki'
    if Path(root).is_symlink() or (hasattr(Path(root),'is_junction') and Path(root).is_junction()) or folder.is_symlink() or (hasattr(folder,'is_junction') and folder.is_junction()):raise ValueError('Folder sesji nie moze byc dowiazaniem.')
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/('sesja-paint-'+secrets.token_hex(5)+'.png')
    with path.open('xb') as stream:Image.new('RGB',(800,500),'white').save(stream,format='PNG')
    trace=Path(root)/'.traces'/('native-'+secrets.token_hex(8))
    if trace.parent.is_symlink() or (hasattr(trace.parent,'is_junction') and trace.parent.is_junction()):raise ValueError('Folder sladow jest dowiazaniem.')
    trace.mkdir(parents=True)
    opened=PaintLauncher().open(path,trace)
    import win32gui
    driver=WindowsVisualDriver(win32gui.GetWindowText(opened['paint_hwnd']),opened['paint_pid'],allow_enter=True)
    return NativeController(driver,path)
