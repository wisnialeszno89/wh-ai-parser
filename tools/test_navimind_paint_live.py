"""Create a window PNG and verify its owned classic Paint window on Windows 10."""
import argparse
import os
import secrets
try:
    from .navimind_paint import DesktopWithPaint,PaintLauncher
    from .run_navimind_desktop_bridge import TableExecutor,NotepadWriter,desktop_path
except ImportError:
    from navimind_paint import DesktopWithPaint,PaintLauncher
    from run_navimind_desktop_bridge import TableExecutor,NotepadWriter,desktop_path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-live',action='store_true')
    args=parser.parse_args()
    if not args.execute_live or os.name!='nt':
        print('Uruchom na Windows: python tools/test_navimind_paint_live.py --execute-live')
        return 2
    agent=DesktopWithPaint(TableExecutor(desktop_path()/'NaviMind-Praca',NotepadWriter()),PaintLauncher())
    task=dict(kind='draw_window_in_paint',folder='Rysunki',file_name='paint-test.png',width_mm=1500,height_mm=1400,construction='double_fixed',frame_color='antracyt')
    result=agent.execute(dict(id=secrets.token_hex(16),task=task,expectedRevision=None))
    print('PAINT_RESULT='+result['status'])
    print(result['message'])
    if result.get('file'):print('PAINT_FILE='+result['file'])
    if result.get('open_status'):print('PAINT_WINDOW='+result['open_status'])
    return 0 if result['status']=='verified' else 6

if __name__=='__main__':raise SystemExit(main())
