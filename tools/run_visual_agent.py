"""First screenshot pilot, scoped to a disposable local lab window."""
import argparse,json,os,sys,tempfile
from datetime import datetime
from uuid import uuid4
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app.agent.visual.runtime import run_visual_task
from app.agent.visual.client import VisualReasoner
from tools import visual_offer_lab

LAB_GOAL='Przygotuj sprawdzony wynik formularza testowego: klient ma nazywać się dokładnie Top Trans, a montaż ma mieć wartość TAK. Zakończ, gdy formularz pokazuje wynik potwierdzający te dane. Nie zamykaj okna.'

def lab_verifier(path,nonce,pid):
    def verify():
        try:state=json.loads(Path(path).read_text(encoding='utf-8'))
        except (OSError,ValueError):return False
        return (state.get('nonce')==nonce and state.get('pid')==pid and state.get('text')=='Top Trans'
                and state.get('checked') is True and state.get('submitted') is True)
    return verify

class LabTrace:
    """Local lab evidence only; no HTTP headers, URLs or credentials."""
    def __init__(self,root):
        self.path=Path(root)/('run-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid4().hex[:8])
        self.path.mkdir(parents=True,exist_ok=False)
        print('VISUAL_TRACE_DIR='+str(self.path.resolve()))
    def __call__(self,turn,frame,action):
        frame.image.save(self.path/f'turn-{turn:02d}.png')
        record={'turn':turn,'image_size':list(frame.image.size),'proposed_action':action}
        token=frame.token
        if token is not None:
            record['window_box']=list(token.window_box);record['view_box']=list(token.view_box)
            if action and action['kind']=='click':
                from app.agent.visual.windows_driver import model_to_window
                x,y=model_to_window(frame,action['x'],action['y'])
                record['requested_desktop_point']=[token.window_box[0]+x,token.window_box[1]+y]
        (self.path/f'turn-{turn:02d}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--state-file',type=Path)
    parser.add_argument('--scenario', choices=('correction', 'offer', 'document', 'order'), default='correction')
    parser.add_argument('--execute-live',action='store_true');parser.add_argument('--max-steps',type=int,default=8)
    parser.add_argument('--trace-dir',type=Path);args=parser.parse_args(argv)
    if os.name!='nt':print('STOP: Windows driver required');return 2
    if args.execute_live and os.getenv('COMPUTER_USE_LIVE')!='1':print('STOP: explicit live authorization required');return 2
    if args.scenario == 'order':
        title, goal, verifier = (
            visual_offer_lab.ORDER_TITLE, visual_offer_lab.ORDER_GOAL, visual_offer_lab.order_verifier
        )
        default_path = visual_offer_lab.ORDER_STATE_FILE
    elif args.scenario == 'document':
        title, goal, verifier = (
            visual_offer_lab.DOCUMENT_TITLE, visual_offer_lab.DOCUMENT_GOAL, visual_offer_lab.document_verifier
        )
        default_path = visual_offer_lab.DOCUMENT_STATE_FILE
    elif args.scenario == 'offer':
        title, goal, verifier = visual_offer_lab.TITLE, visual_offer_lab.GOAL, visual_offer_lab.offer_verifier
        default_path = visual_offer_lab.STATE_FILE
    else:
        title, goal, verifier = 'NaviMind Visual Lab', LAB_GOAL, lab_verifier
        default_path = Path(tempfile.gettempdir()) / 'navimind-visual-lab.json'
    state_path = args.state_file or default_path
    try:
        state=json.loads(state_path.read_text(encoding='utf-8'))
        if not isinstance(state, dict) or state.get('title')!=title or type(state.get('pid')) is not int or not isinstance(state.get('nonce'),str):raise ValueError('visual_lab_state_invalid')
        if args.scenario in {'document', 'order'} and not visual_offer_lab.document_start_ready(state):
            raise ValueError('visual_document_start_not_fresh_reopen_lab')
        from app.agent.visual.windows_driver import WindowsVisualDriver
        replace_focused_text = (
            visual_offer_lab.order_numeric_focus(state_path, state['nonce'], state['pid'])
            if args.scenario == 'order' else None
        )
        driver=WindowsVisualDriver(state['title'],state['pid'],allow_enter=True,
                                   replace_focused_text=replace_focused_text)
        if args.scenario in {'document', 'order'}:
            print('VISUAL_DOCUMENT_START=fresh')
        print('VISUAL_SCREENSHOTS_SENT=True SCOPE=local_test_lab')
        trace=LabTrace(args.trace_dir) if args.trace_dir else None
        observe = (
            visual_offer_lab.document_observer(state_path, state['nonce'], state['pid'], title=title)
            if args.scenario in {'document', 'order'} else None
        )
        result=run_visual_task(driver,VisualReasoner(),goal,execute=args.execute_live,max_steps=args.max_steps,
                               verify=verifier(state_path,state['nonce'],state['pid']),trace=trace,observe=observe)
        print('VISUAL_FINAL_STATUS='+result)
        return 0 if result in ('proposed','verified') else 6
    except (ValueError,RuntimeError,OSError) as exc:print('VISUAL_STOP='+str(exc));return 6
if __name__=='__main__':raise SystemExit(main())
