"""Check protected visual endpoint without a screenshot or model request."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app.agent.visual.client import VisualReasoner

def main():
    print('VISUAL_PROBE_SCREENSHOTS_SENT=False MODEL_REQUESTS=0')
    try:result=VisualReasoner().probe()
    except (ValueError,RuntimeError,OSError) as exc:
        print('VISUAL_CONNECTION_STOP='+str(exc));return 6
    print('VISUAL_CONNECTION='+result)
    return 0 if result=='ready' else 6

if __name__=='__main__':raise SystemExit(main())
