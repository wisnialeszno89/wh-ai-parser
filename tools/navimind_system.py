"""Read-only technical facts; no process names, accounts, keys or network identifiers."""
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import threading
from datetime import datetime,timezone


def collect_facts():
    memory=None
    if os.name=='nt':
        class Memory(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong),*[(name,ctypes.c_ulonglong) for name in ['total_physical','available_physical','total_page','available_page','total_virtual','available_virtual','available_extended']]]
        value=Memory();value.length=ctypes.sizeof(value)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)):memory={'total_bytes':value.total_physical,'available_bytes':value.available_physical,'load_percent':value.load}
    drive=os.environ.get('SystemDrive','C:')+'\\' if os.name=='nt' else '/'
    disk=shutil.disk_usage(drive)
    return {'schema':1,'observed_at':datetime.now(timezone.utc).isoformat(),'os':{'system':platform.system(),'release':platform.release(),'version':platform.version(),'architecture':platform.machine()},'cpu':{'logical_processors':os.cpu_count()},'memory':memory,'system_disk':{'total_bytes':disk.total,'free_bytes':disk.free},'python':platform.python_version(),'tools':{name:importlib.util.find_spec(name) is not None for name in ['PIL','pywinauto','playwright']},'limits':['Brak pomiaru zuzycia CPU przez procesy, SMART dysku i skanowania malware.','Raport nie ustala samodzielnie przyczyny problemu i nie zmienia ustawien.']}


class DesktopWithDiagnostics:
    def __init__(self,tables,collector=collect_facts):
        self.tables,self.collector=tables,collector;self.root=tables.root;self.results=tables.results;self.lock=threading.Lock()
    def __getattr__(self,name):return getattr(self.tables,name)
    def status(self):
        s=self.tables.status();return {**s,'capabilities':[*s['capabilities'],'inspect_computer']}
    def execute(self,body):
        if not isinstance(body,dict) or not isinstance(body.get('task'),dict) or body['task'].get('kind')!='inspect_computer':return self.tables.execute(body)
        task=body['task']
        if set(body)!={'id','task','expectedRevision'} or not isinstance(body['id'],str) or not re.fullmatch(r'[a-zA-Z0-9-]{16,80}',body['id']) or body['expectedRevision'] is not None or set(task)!={'kind','folder','file_name'}:raise ValueError('Nieprawidlowe zadanie diagnostyki.')
        for key in ('folder','file_name'):
            name=task[key]
            if not isinstance(name,str) or not 1<=len(name)<=60 or name!=name.strip() or name.endswith('.') or name in {'.','..'} or re.search(r'[<>:"/\\|?*\x00-\x1f]',name) or re.match(r'^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)',name,re.I):raise ValueError('Nieprawidlowa nazwa raportu.')
        if not task['file_name'].lower().endswith('.json') or len(task['file_name'])<=5:raise ValueError('Raport wymaga nazwy .json.')
        fingerprint=hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        with self.lock:
            cached=self.results.get(body['id'])
            if cached:return cached[1] if cached[0]==fingerprint else {'status':'review','message':'Identyfikator nalezy do innego zadania.'}
            if len(self.results)>=500:raise ValueError('Uruchom nowa sesje wykonawcy.')
            result={'status':'review','message':'Rozpoczeto odczyt; nie ponawiaj automatycznie.'};self.results[body['id']]=(fingerprint,result)
            try:
                folder=self.root/task['folder']
                for p in [self.root,folder]:
                    if p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()):raise ValueError('Raport nie moze trafic do dowiazania.')
                if folder.resolve().parent!=self.root.resolve():raise ValueError('Raport poza obszarem pracy.')
                folder.mkdir(parents=True,exist_ok=True)
                index=1
                while True:
                    name=task['file_name'] if index==1 else Path(task['file_name']).stem[:48]+'-'+str(index)+'.json'
                    path=folder/name
                    if path.is_symlink():raise ValueError('Plik raportu jest dowiazaniem.')
                    if not path.exists():break
                    index+=1
                    if index>1000:raise ValueError('Brak wolnej nazwy raportu.')
                facts=self.collector()
                with path.open('x',encoding='utf-8') as output:json.dump(facts,output,ensure_ascii=False,indent=2)
                if json.loads(path.read_text(encoding='utf-8'))!=facts:raise ValueError('Nie potwierdzono zapisu raportu.')
                result={'status':'verified','message':'Odczytano fakty i sprawdzono zapis raportu. Ustawienia komputera pozostaly bez zmian.','file':str(path),'system_report':facts}
            except Exception as exc:result={'status':'review','message':str(exc)[:500]}
            self.results[body['id']]=(fingerprint,result);return result
