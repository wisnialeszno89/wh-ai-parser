"""Real Chromium smoke test for Windows; no customer data or payment actions."""
from pathlib import Path
import argparse
import secrets
try:
    from .navimind_browser import BrowserController
except ImportError:
    from navimind_browser import BrowserController


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-live',action='store_true')
    parser.add_argument('--headless',action='store_true',help='Run the same Chromium regression without a visible window (CI).')
    args=parser.parse_args()
    if not args.execute_live:
        print('Uruchom z --execute-live, aby otworzyć osobne testowe okno Chromium.')
        return 2
    from playwright.sync_api import sync_playwright
    with sync_playwright() as runtime:
        browser=runtime.chromium.launch(headless=args.headless)
        try:
            page=browser.new_page(viewport={'width':1280,'height':850})
            page.set_content(Path(__file__).with_name('navimind_browser_lab.html').read_text(encoding='utf-8'))
            agent=BrowserController(page)
            def step(kind,name=None,**fields):
                snapshot=agent.observe()
                if name is not None:
                    matches=[c for c in snapshot['controls'] if c['name']==name]
                    if len(matches)!=1:raise RuntimeError('Niejednoznaczny element: '+name)
                    fields['ref']=matches[0]['ref']
                result=agent.execute(dict(id=secrets.token_hex(16),task=dict(kind=kind,**fields),expectedRevision=snapshot['revision']))
                if result['status']!='verified':raise RuntimeError(result['message'])
                return result['browser']
            step('browser_fill','Wyszukaj klienta',text='Top Trans')
            step('browser_click','Top Trans')
            step('browser_fill','Szerokość [mm]',text='1100')
            step('browser_fill','Wysokość [mm]',text='1000')
            step('browser_select','Kolor zewnętrzny',value='antracyt')
            step('browser_select','Otwieranie',value='DKR')
            final=step('browser_click','Pokaż podgląd')
            for expected in ['PODGLĄD GOTOWY','Klient: Top Trans','Szerokość: 1100 mm','Wysokość: 1000 mm','Kolor: antracyt','Okucie: DKR']:
                if expected not in final['text']:raise RuntimeError('Brak potwierdzenia: '+expected)
            print('BROWSER_LAB_RESULT=verified STEPS=7 CUSTOMER=Top_Trans WIDTH=1100 HEIGHT=1000 COLOR=antracyt OPENING=DKR')
            # Reproduce a second command after the operator/preview scrolled the
            # viewport away from the fields. No form reset or restart is used.
            page.set_viewport_size({'width':1280,'height':360})
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            if page.locator('#width').bounding_box()['y']>=0:
                raise RuntimeError('Regression setup did not move the width field above the viewport.')
            step('browser_fill','Szerokość [mm]',text='1230')
            changed=agent.observe()
            if 'PODGLĄD GOTOWY' in changed['text']:
                raise RuntimeError('A previous preview remained marked ready after a field changed.')
            final=step('browser_click','Pokaż podgląd')
            for expected in ['PODGLĄD GOTOWY','Klient: Top Trans','Szerokość: 1230 mm','Wysokość: 1000 mm','Kolor: antracyt','Okucie: DKR']:
                if expected not in final['text']:raise RuntimeError('Correction lost source data: '+expected)
            for field,value in [('width','1230'),('height','1000'),('color','antracyt'),('opening','DKR')]:
                if page.locator('#'+field).input_value()!=value:raise RuntimeError('Correction changed an unrelated field: '+field)
            print('BROWSER_CORRECTION_RESULT=verified WIDTH=1230 HEIGHT=1000 COLOR=antracyt OPENING=DKR CUSTOMER=Top_Trans')
            print('FINANCIAL_ACTIONS_EXECUTED=False')
        finally:browser.close()
    return 0

if __name__=='__main__':raise SystemExit(main())
