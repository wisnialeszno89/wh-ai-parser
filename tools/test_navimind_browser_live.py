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
    args=parser.parse_args()
    if not args.execute_live:
        print('Uruchom z --execute-live, aby otworzyć osobne testowe okno Chromium.')
        return 2
    from playwright.sync_api import sync_playwright
    with sync_playwright() as runtime:
        browser=runtime.chromium.launch(headless=False)
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
            print('FINANCIAL_ACTIONS_EXECUTED=False')
        finally:browser.close()
    return 0

if __name__=='__main__':raise SystemExit(main())
