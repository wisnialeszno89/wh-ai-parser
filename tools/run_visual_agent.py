"""First screenshot pilot, scoped to a disposable local lab window."""
import argparse,json,os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app.agent.visual.runtime import run_visual_task
from app.agent.visual.client import VisualReasoner

LAB_GOAL='Przygotuj sprawdzony wynik formularza testowego: klient ma nazywać się dokładnie Top Trans, a montaż ma mieć wartość TAK. Zakończ, gdy formularz pokazuje wynik potwierdzający te dane. Nie zamykaj okna.'

def lab_verifier(path,nonce,pid):
    def verify():
        try:state=json.loads(Path(path).read_text(encoding='utf-8'))
        except (OSError,ValueError):return False
        return (state.get('nonce')==nonce and state.get('pid')==pid and state.get('text')=='Top Trans'
                and state.get('checked') is True and state.get('submitted') is True)
    return verify

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--state-file',type=Path,default=Path(tempfile.gettempdir())/'navimind-visual-lab.json')
    parser.add_argument('--execute-live',action='store_true');parser.add_argument('--max-steps',type=int,default=16);args=parser.parse_args(argv)
    if os.name!='nt':print('STOP: Windows driver required');return 2
    if args.execute_live and os.getenv('COMPUTER_USE_LIVE')!='1':print('STOP: explicit live authorization required');return 2
    try:
        state=json.loads(args.state_file.read_text(encoding='utf-8'))
        if state.get('title')!='NaviMind Visual Lab' or type(state.get('pid')) is not int or not isinstance(state.get('nonce'),str):raise ValueError('visual_lab_state_invalid')
        from app.agent.visual.windows_driver import WindowsVisualDriver
        driver=WindowsVisualDriver(state['title'],state['pid'],allow_enter=True)
        print('VISUAL_SCREENSHOTS_SENT=True SCOPE=local_test_lab')
        result=run_visual_task(driver,VisualReasoner(),LAB_GOAL,execute=args.execute_live,max_steps=args.max_steps,
                               verify=lab_verifier(args.state_file,state['nonce'],state['pid']))
        print('VISUAL_FINAL_STATUS='+result)
        return 0 if result in ('proposed','verified') else 6
    except (ValueError,RuntimeError,OSError) as exc:print('VISUAL_STOP='+str(exc));return 6
if __name__=='__main__':raise SystemExit(main())
