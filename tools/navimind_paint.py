"""Window sketch pilot: render a checked PNG and open an owned Windows 10 Paint window."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import threading
import time

CONSTRUCTIONS={'single_dkl','single_dkr','double_fixed'}
COLORS={'bialy':'#f4f4f4','antracyt':'#3c4144','mahon':'#813f2e'}
LABELS={'single_dkl':'Jednoskrzydlowe DKL','single_dkr':'Jednoskrzydlowe DKR','double_fixed':'Dwuskrzydlowe - slupek staly'}
WIDTH,HEIGHT=720,480


def validate_paint_task(task):
    expected={'kind','folder','file_name','width_mm','height_mm','construction','frame_color'}
    if not isinstance(task,dict) or set(task)!=expected or task['kind']!='draw_window_in_paint':
        raise ValueError('Nieprawidłowe zadanie rysunku.')
    for key in ('folder','file_name'):
        value=task[key]
        if not isinstance(value,str) or not 1<=len(value)<=60 or value!=value.strip() or value.endswith('.') or value in {'.','..'} or re.search(r'[<>:"/\\|?*\x00-\x1f]',value) or re.match(r'^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)',value,re.I):
            raise ValueError('Nieprawidłowa nazwa folderu lub pliku rysunku.')
    if not task['file_name'].lower().endswith('.png') or len(task['file_name'])<=4:
        raise ValueError('Rysunek wymaga nazwy pliku .png.')
    for key in ('width_mm','height_mm'):
        if type(task[key]) is not int or not 100<=task[key]<=10000:
            raise ValueError('Wymiary rysunku muszą wynosić 100–10000 mm.')
    if not isinstance(task['construction'],str) or task['construction'] not in CONSTRUCTIONS or not isinstance(task['frame_color'],str) or task['frame_color'] not in COLORS:
        raise ValueError('Wybierz obsługiwany schemat i kolor.')
    # Extremely flat shapes cannot show hardware legibly at the pilot canvas size.
    ratio=task['width_mm']/task['height_mm']
    if not .25<=ratio<=4:
        raise ValueError('Ten pilot obsługuje proporcje szerokość/wysokość od 1:4 do 4:1.')
    return task


def geometry(task):
    validate_paint_task(task)
    scale=min(510/task['width_mm'],300/task['height_mm'])
    w,h=round(task['width_mm']*scale),round(task['height_mm']*scale)
    left,top=(WIDTH-w)//2,80+(300-h)//2
    outer=(left,top,left+w,top+h)
    thickness=max(6,min(16,round(min(w,h)*.06)))
    fields=[]
    count=2 if task['construction']=='double_fixed' else 1
    for index in range(count):
        x1=left+thickness+round(index*(w-2*thickness)/count)
        x2=left+thickness+round((index+1)*(w-2*thickness)/count)
        if count==2:
            if index==0:x2-=thickness//2
            else:x1+=thickness//2
        box=(x1,top+thickness,x2,top+h-thickness)
        opening=('DKL' if index==0 else 'DKR') if count==2 else ('DKL' if task['construction']=='single_dkl' else 'DKR')
        fields.append({'box':box,'opening':opening,'hinge_side':'LEFT' if opening=='DKL' else 'RIGHT','handle_side':'RIGHT' if opening=='DKL' else 'LEFT'})
    return {'canvas':[WIDTH,HEIGHT],'outer':outer,'frame_thickness':thickness,'fields':fields,'view':'inside'}


def render(task):
    from PIL import Image,ImageDraw,ImageFont
    plan=geometry(task)
    image=Image.new('RGB',(WIDTH,HEIGHT),'white');d=ImageDraw.Draw(image)
    try:
        font=ImageFont.truetype(str(Path(os.environ.get('SystemRoot','/nonexistent'))/'Fonts'/'arial.ttf'),16)
    except OSError:
        try:font=ImageFont.truetype('DejaVuSans.ttf',16)
        except OSError:font=ImageFont.load_default()
    try:small=ImageFont.truetype('DejaVuSans.ttf',12)
    except OSError:small=font
    def centered(text,y,face=font):
        box=d.textbbox((0,0),text,font=face);d.text(((WIDTH-(box[2]-box[0]))//2,y),text,fill='#192b3a',font=face)
    centered('NaviMind - schemat okna',16)
    centered('Widok od wewnatrz - rysunek pogladowy',42,small)
    color=COLORS[task['frame_color']];t=plan['frame_thickness']
    d.rectangle(plan['outer'],fill=color,outline='black',width=2)
    for field in plan['fields']:
        a,b,c,e=field['box']
        d.rectangle((a,b,c,e),fill=color,outline='#202020',width=2)
        inset=max(3,t//2);glass=(a+inset,b+inset,c-inset,e-inset)
        d.rectangle(glass,fill='#d8effa',outline='#202020',width=1)
        gx,gy,gr,gb=glass;middle=(gy+gb)//2
        middle=(glass[1]+glass[3])//2
        # Show hinges and the opposite handle, without inventing a WH opening symbol.
        hinge_x=a+2 if field['hinge_side']=='LEFT' else c-2
        for hinge_y in (b+max(5,(e-b)//5),e-max(5,(e-b)//5)):
            d.rectangle((hinge_x-2,hinge_y-5,hinge_x+2,hinge_y+5),fill='#777777',outline='#111111')
        gx,gy,gr,gb=glass
        hx=c-3 if field['handle_side']=='RIGHT' else a+3
        d.rectangle((hx-2,middle-9,hx+2,middle+10),fill='#eeeeee',outline='#111111')
        d.line([(hx,middle),(hx+(7 if field['handle_side']=='LEFT' else -7),middle)],fill='#111111',width=3)
        d.text((gx+5,gy+5),field['opening'],fill='#1d3445',font=small)
    left,top,right,bottom=plan['outer']
    d.line([(left,bottom+15),(right,bottom+15)],fill='black',width=1)
    for x in (left,right):d.line([(x,bottom+9),(x,bottom+21)],fill='black',width=1)
    centered(str(task['width_mm'])+' mm',bottom+25)
    d.line([(right+20,top),(right+20,bottom)],fill='black',width=1)
    d.text((right+25,(top+bottom)//2),str(task['height_mm'])+' mm',fill='black',font=small)
    centered('Kolor ramy: '+task['frame_color']+' | '+LABELS[task['construction']],432,small)
    return image,plan


def pixel_digest(image):
    return hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()


def verify_image(path,expected):
    from PIL import Image
    if path.stat().st_size>2*1024*1024:
        raise ValueError('Nieprawidlowy rozmiar zapisanego rysunku.')
    with Image.open(path) as actual:
        actual.load()
        if actual.format!='PNG' or actual.size!=(WIDTH,HEIGHT) or pixel_digest(actual)!=pixel_digest(expected):
            raise ValueError('Zapisany obraz nie zgadza sie z przygotowanym rysunkiem.')


class PaintLauncher:
    """Only a new classic Paint process/window is accepted; no keystrokes sent to existing windows."""
    def __init__(self):self.windows=[]
    def open(self,path,trace):
        import win32gui
        import win32process
        from pywinauto import Application
        exe=Path(os.environ['SystemRoot'])/'System32'/'mspaint.exe'
        process=subprocess.Popen([str(exe),str(path)])
        app=Application(backend='win32').connect(process=process.pid,timeout=12)
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            windows=[w for w in app.windows() if w.is_visible() and w.class_name()=='MSPaintApp']
            if len(windows)==1 and any(name.casefold() in windows[0].window_text().casefold() for name in (path.name,path.stem)):
                window=windows[0]
                if win32process.GetWindowThreadProcessId(window.handle)[1]!=process.pid:
                    raise RuntimeError('Nie potwierdzono nowego procesu Painta.')
                window.maximize()
                window.set_focus()
                if win32gui.GetForegroundWindow()!=window.handle:
                    raise RuntimeError('Nowe okno Painta nie uzyskalo fokusu.')
                self.windows.append((process.pid,window.handle))
                window.capture_as_image().save(trace/'paint-opened.png')
                return {'open_status':'verified','paint_pid':process.pid,'paint_hwnd':window.handle}
            time.sleep(.2)
        raise RuntimeError('Nie potwierdzono pliku w nowym oknie klasycznego Painta Windows 10. Obraz PNG jest zapisany.')


class DesktopWithPaint:
    def __init__(self,tables,launcher):
        self.tables,self.launcher=tables,launcher
        self.results=tables.results;self.root=tables.root
        self.lock=threading.Lock()
    def status(self):
        status=self.tables.status()
        return {**status,'capabilities':[*status['capabilities'],'draw_window_in_paint'],'paint':{'available':True,'method':'render_png_open_paint'}}
    def safe_path(self,folder,name):
        path=self.root/folder/name
        for item in (self.root,path.parent,path):
            if item.is_symlink() or (hasattr(item,'is_junction') and item.is_junction()):
                raise ValueError('Folder ani plik rysunku nie moze byc dowiazaniem.')
        if path.resolve().parent.parent!=self.root.resolve():
            raise ValueError('Rysunek musi pozostac w obszarze NaviMind-Praca.')
        return path
    def execute(self,body):
        if not isinstance(body,dict) or not isinstance(body.get('task'),dict) or body['task'].get('kind')!='draw_window_in_paint':
            return self.tables.execute(body)
        if set(body)!={'id','task','expectedRevision'} or not isinstance(body['id'],str) or not re.fullmatch(r'[a-zA-Z0-9-]{16,80}',body['id']) or body['expectedRevision'] is not None:
            raise ValueError('Nieprawidlowe zadanie nowego rysunku.')
        task=validate_paint_task(body['task'])
        fingerprint=hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        with self.lock:
            cached=self.results.get(body['id'])
            if cached:
                if cached[0]!=fingerprint:return {'status':'review','message':'Identyfikator nalezy do innego zadania.'}
                return cached[1]
            if len(self.results)>=500:raise ValueError('Uruchom nowa sesje wykonawcy.')
            result={'status':'review','message':'Rozpoczeto przygotowanie rysunku. Nie ponawiaj automatycznie.'}
            self.results[body['id']]=(fingerprint,result)
            target=None
            try:
                original=Path(task['file_name']);index=1
                while True:
                    name=original.name if index==1 else original.stem[:48]+'-'+str(index)+'.png'
                    target=self.safe_path(task['folder'],name)
                    meta=self.safe_path(task['folder'],name+'.json')
                    if not target.exists() and not meta.exists():break
                    index+=1
                    if index>1000:raise ValueError('Nie znaleziono wolnej nazwy rysunku.')
                image,plan=render(task)
                trace_root=self.root/'.traces'
                if trace_root.is_symlink() or (hasattr(trace_root,'is_junction') and trace_root.is_junction()):
                    raise ValueError('Folder sladow nie moze byc dowiazaniem.')
                trace=trace_root/body['id']
                trace.mkdir(parents=True,exist_ok=False)
                staged=trace/'rendered.png';image.save(staged,format='PNG');verify_image(staged,image)
                target.parent.mkdir(parents=True,exist_ok=True)
                self.safe_path(task['folder'],target.name)
                with target.open('xb') as output:output.write(staged.read_bytes())
                verify_image(target,image)
                with meta.open('x',encoding='utf-8') as output:json.dump({'task':task,'geometry':plan,'pixel_sha256':pixel_digest(image),'method':'render_png_open_paint'},output,ensure_ascii=False,indent=2)
                opened=self.launcher.open(target,trace)
                if opened.get('open_status')!='verified':raise RuntimeError('Nie potwierdzono nowego okna Painta. Obraz PNG jest zapisany.')
                verify_image(target,image)
                result={'status':'verified','message':'Wygenerowano i odczytano schemat PNG. Potwierdzono plik w nowym oknie Painta.','file':str(target),'drawing':{**task,'canvas_px':[WIDTH,HEIGHT],'hinges_and_handles':plan['fields'],'method':'render_png_open_paint'},**opened}
            except Exception as exc:
                result={'status':'review','message':str(exc)[:600]}
                if target is not None and target.is_file():result['file']=str(target)
            self.results[body['id']]=(fingerprint,result)
            return result
