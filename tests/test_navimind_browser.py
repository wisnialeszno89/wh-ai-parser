"""Browser boundary tests use a small DOM adapter; native Chromium is tested by the live smoke tool."""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.navimind_browser import BrowserController, public_url, validate_browser_task


def control(name, tag='button', type='button', value=None, **kw):
    return dict(tag=tag,role='',type=type,name=name,href='',disabled=False,checked=False,autocomplete='',context='',value=value,options=None,**kw)


class Handle:
    def __init__(self,page,record):self.page,self.record=page,record
    def evaluate(self,_):return self.record in self.page.controls
    def is_visible(self):return True
    def is_enabled(self):return not self.record['disabled']
    def dispose(self):pass
    def fill(self,value):self.page.fills+=1;self.record['value']=value
    def input_value(self):return self.record['value']
    def select_option(self,value):self.record['value']=value
    def click(self,**_):self.page.clicks+=1;self.page.text='Menu otwarte'


class Page:
    def __init__(self):
        self.url='https://example.org/orders?session=private-token'
        self.text='Orders';self.controls=[control('Menu akcji'),control('Szerokość','input','number','')]
        self.clicks=0;self.fills=0
    def wait_for_timeout(self,_):pass
    def set_default_timeout(self,_):pass
    def set_default_navigation_timeout(self,_):pass
    def on(self,*_):pass
    def is_closed(self):return False
    def locator(self,_):return self
    def element_handles(self):return [Handle(self,c) for c in self.controls]
    def evaluate(self,script,handles):
        return dict(title='Test',text=self.text,scroll_y=0,controls=[dict(index=i,**copy.deepcopy(h.record)) for i,h in enumerate(handles)])
    def goto(self,url,**_):self.url=url;self.text='Nowa strona'


class BrowserTests(unittest.TestCase):
    def setUp(self):self.page=Page();self.agent=BrowserController(self.page);self.serial=0
    def job(self,snapshot,task):
        self.serial+=1
        return dict(id=f'browser-test-{self.serial:016}',task=task,expectedRevision=snapshot['revision'])
    def test_snapshot_omits_fields_and_session_queries(self):
        self.page.controls.append(control('Hasło','input','password','a-private-password'))
        s=self.agent.observe();serialized=json.dumps(s)
        self.assertNotIn('a-private-password',serialized);self.assertNotIn('private-token',serialized)
        self.assertNotIn('context',serialized);self.assertNotIn('options',s['controls'][0])
    def test_click_is_bound_to_current_view_and_idempotent(self):
        s=self.agent.observe();body=self.job(s,dict(kind='browser_click',ref=s['controls'][0]['ref']))
        r=self.agent.execute(body);self.assertEqual(r['status'],'verified');self.assertEqual(r['browser']['text'],'Menu otwarte')
        self.assertEqual(self.agent.execute(body),r);self.assertEqual(self.page.clicks,1)
        changed={**body,'task':dict(kind='browser_back')};self.assertEqual(self.agent.execute(changed)['status'],'review')
    def test_changed_page_blocks_click(self):
        s=self.agent.observe();self.page.text='Inne zamówienie'
        r=self.agent.execute(self.job(s,dict(kind='browser_click',ref=s['controls'][0]['ref'])))
        self.assertEqual(r['status'],'review');self.assertEqual(self.page.clicks,0)
    def test_reobserved_reference_cannot_hit_another_element(self):
        first=self.agent.observe();second=self.agent.observe()
        r=self.agent.execute(self.job(second,dict(kind='browser_click',ref=first['controls'][0]['ref'])))
        self.assertEqual(r['status'],'review');self.assertEqual(self.page.clicks,0)
    def test_filling_is_read_back_but_not_published(self):
        s=self.agent.observe();r=self.agent.execute(self.job(s,dict(kind='browser_fill',ref=s['controls'][1]['ref'],text='1100')))
        self.assertEqual(r['status'],'verified');self.assertEqual(self.page.controls[1]['value'],'1100')
        self.assertNotIn('1100',json.dumps(r['browser']))
    def test_sensitive_controls_and_submit_never_click(self):
        for item in [control('Refund'),control('Potwierdź zwrot'),control('Zwykły formularz',type='submit'),control('Usuń pozycję'),control('Payout')]:
            with self.subTest(name=item['name']):
                self.page.controls=[item];s=self.agent.observe();r=self.agent.execute(self.job(s,dict(kind='browser_click',ref=s['controls'][0]['ref'])))
                self.assertEqual(r['status'],'review');self.assertEqual(self.page.clicks,0)
    def test_password_and_otp_fields_are_not_filled(self):
        for item in [control('Hasło','input','password',''),control('OTP','input','text','')]:
            self.page.controls=[item];s=self.agent.observe();r=self.agent.execute(self.job(s,dict(kind='browser_fill',ref=s['controls'][0]['ref'],text='123456')))
            self.assertEqual(r['status'],'review');self.assertEqual(self.page.fills,0)
    def test_select_only_observed_option(self):
        self.page.controls=[control('Kolor','select','select-one','',options_override=True)]
        self.page.controls[0].pop('options_override');self.page.controls[0]['options']=[dict(label='Antracyt',value='antracyt')]
        s=self.agent.observe();r=self.agent.execute(self.job(s,dict(kind='browser_select',ref=s['controls'][0]['ref'],value='unknown')))
        self.assertEqual(r['status'],'review')
        s=self.agent.observe();r=self.agent.execute(self.job(s,dict(kind='browser_select',ref=s['controls'][0]['ref'],value='antracyt')))
        self.assertEqual(r['status'],'verified')
    def test_cross_domain_links_require_an_explicit_navigation_command(self):
        self.page.controls=[control('Następna strona')];self.page.controls[0]['href']='https://other.example/orders'
        snapshot=self.agent.observe();r=self.agent.execute(self.job(snapshot,dict(kind='browser_click',ref=snapshot['controls'][0]['ref'])))
        self.assertEqual(r['status'],'review');self.assertEqual(self.page.clicks,0)

    def test_script_and_raw_selectors_are_not_tasks(self):
        for task in [dict(kind='shell',command='whoami'),dict(kind='browser_click',selector='body'),dict(kind='browser_evaluate',script='anything')]:
            with self.assertRaises(ValueError):validate_browser_task(task)
    def test_public_navigation_rejects_local_files_credentials_and_local_addresses(self):
        self.assertEqual(public_url('https://example.org/orders'),'https://example.org/orders')
        for url in ['file:///C:/Windows','javascript:alert(1)','http://localhost','http://127.0.0.1','http://10.0.0.1','http://169.254.169.254','http://0177.0.0.1','http://0x7f.0.0.1','https://u:p@example.org','https://example.org:43127']:
            with self.subTest(url=url),self.assertRaises(ValueError):public_url(url)

if __name__=='__main__':unittest.main()


def test_saved_browser_view_is_local_read_back_and_idempotent(tmp_path):
    from io import BytesIO
    from PIL import Image
    page = Page()
    stream = BytesIO()
    Image.new('RGB', (100, 80), 'white').save(stream, format='PNG')
    captures = []
    def screenshot(**kwargs):
        captures.append(kwargs)
        return stream.getvalue()
    page.screenshot = screenshot
    agent = BrowserController(page)
    agent.export_root = tmp_path
    view = agent.observe()
    body = dict(id='save-view-test-000001', task=dict(kind='browser_save_snapshot'), expectedRevision=view['revision'])
    result = agent.execute(body)
    assert result['status'] == 'verified'
    saved = result['browser_export']
    assert Path(saved['image_file']).is_file()
    report = json.loads(Path(saved['report_file']).read_text(encoding='utf-8'))
    assert report['url'] == 'https://example.org/orders'
    assert report['price_verified'] is False and report['goal_verified'] is False
    assert 'private-token' not in json.dumps(report)
    assert agent.execute(body) == result and len(captures) == 1
    assert page.clicks == 0 and page.fills == 0


def test_export_rejects_paths_and_changed_view(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        validate_browser_task(dict(kind='browser_save_snapshot', path='C:/Windows/test.png'))
    from io import BytesIO
    from PIL import Image
    stream=BytesIO();Image.new('RGB',(10,10),'white').save(stream,format='PNG')
    page=Page()
    def screenshot(**kwargs):
        page.text='Changed during capture'
        return stream.getvalue()
    page.screenshot=screenshot
    agent=BrowserController(page);agent.export_root=tmp_path
    view=agent.observe()
    result=agent.execute(dict(id='save-changed-view-0001',task=dict(kind='browser_save_snapshot'),expectedRevision=view['revision']))
    assert result['code']=='STALE_PAGE' and not list(tmp_path.rglob('*.png'))


def test_submit_type_without_form_is_a_normal_configuration_button():
    page = Page()
    page.controls = [control('1-flg. Dreh-Kipp', type='submit', submits_form=False)]
    agent = BrowserController(page)
    view = agent.observe()
    assert view['controls'][0]['submits_form'] is False
    result = agent.execute(dict(id='outside-form-button-01', task=dict(kind='browser_click', ref=view['controls'][0]['ref']), expectedRevision=view['revision']))
    assert result['status'] == 'verified' and page.clicks == 1


def test_real_form_submission_remains_blocked_and_names_target():
    page = Page()
    page.controls = [control('Konfiguruj', type='submit', submits_form=True)]
    agent = BrowserController(page)
    view = agent.observe()
    result = agent.execute(dict(id='inside-form-button-001', task=dict(kind='browser_click', ref=view['controls'][0]['ref']), expectedRevision=view['revision']))
    assert result['status'] == 'review' and page.clicks == 0
    assert 'Konfiguruj' in result['message'] and 'formularza' in result['message']
