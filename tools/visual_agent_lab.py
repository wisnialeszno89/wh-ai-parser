"""Disposable GUI task with independent state verification. No WindowHub data."""
import argparse,json,os,secrets,tempfile
from pathlib import Path

class LabState:
    def __init__(self,nonce=None):
        self.nonce=nonce or secrets.token_hex(16);self.text='ATop Trans';self.checked=False;self.submitted=False
    def snapshot(self):
        return dict(nonce=self.nonce,pid=os.getpid(),title='NaviMind Visual Lab',text=self.text,checked=self.checked,submitted=self.submitted)
    def save(self,path):
        path=Path(path);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(self.snapshot()),encoding='utf-8');os.replace(temp,path)

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--state-file',type=Path,default=Path(tempfile.gettempdir())/'navimind-visual-lab.json');args=parser.parse_args(argv)
    import tkinter as tk
    state=LabState();root=tk.Tk();root.title('NaviMind Visual Lab');root.geometry('680x400+100+100')
    root.configure(padx=28,pady=22)
    tk.Label(root,text='Formularz testowy — dane fikcyjne',font=('Arial',18)).pack(anchor='w',pady=(0,18))
    tk.Label(root,text='Nazwa klienta',font=('Arial',12)).pack(anchor='w')
    value=tk.StringVar(value=state.text);checked=tk.BooleanVar(value=False)
    tk.Entry(root,textvariable=value,font=('Arial',16),width=32).pack(anchor='w',pady=(4,14))
    tk.Checkbutton(root,text='Montaż',variable=checked,font=('Arial',13)).pack(anchor='w')
    result=tk.Label(root,text='Wynik: jeszcze nie sprawdzono',font=('Arial',12),wraplength=600,justify='left')
    def edit(*unused):
        state.text=value.get();state.checked=checked.get();state.submitted=False;state.save(args.state_file)
    def submit():
        state.text=value.get();state.checked=checked.get();state.submitted=True;state.save(args.state_file)
        result.config(text='Wynik: klient = '+state.text+'; montaż = '+('TAK' if state.checked else 'NIE'))
    tk.Button(root,text='Sprawdź',command=submit,font=('Arial',13)).pack(anchor='w',pady=14);result.pack(anchor='w')
    value.trace_add('write',edit);checked.trace_add('write',edit);state.save(args.state_file)
    print('VISUAL_LAB_STATE_FILE='+str(args.state_file),flush=True)
    root.mainloop()

if __name__=='__main__':main()
