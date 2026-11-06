"""Bounded image/action protocol shared with NaviMind visual-task endpoint."""
import base64,struct
KINDS={'click','type_text','key','scroll','wait','inspect','done','ask_user'}
KEYS={'CTRL+A','BACKSPACE','HOME','END','TAB','ESC','ENTER'}
FIELDS={'kind','x','y','width','height','text','key','direction','amount','reason'}

def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi: raise ValueError('visual_integer_invalid')

def text(v,limit):
    if not isinstance(v,str) or not v.strip() or len(v)>limit: raise ValueError('visual_text_invalid')

def validate_request(r):
    if not isinstance(r,dict) or set(r)!={'version','task_id','turn','goal','screen','feedback'}: raise ValueError('visual_request_fields')
    if r['version']!='visual-1':raise ValueError('visual_version')
    text(r['task_id'],128);text(r['goal'],8000);integer(r['turn'],0,29)
    s=r['screen']
    if not isinstance(s,dict) or set(s)!={'image_data_url','width','height'}:raise ValueError('visual_screen_fields')
    integer(s['width'],1,1600);integer(s['height'],1,1200)
    if not isinstance(s['image_data_url'],str) or not s['image_data_url'].startswith('data:image/png;base64,'):raise ValueError('visual_png_required')
    encoded=s['image_data_url'][22:]
    if len(encoded)>2800000:raise ValueError('visual_image_too_large')
    png=base64.b64decode(encoded,validate=True)
    if len(png)<24 or len(png)>2*1024*1024 or png[:8]!=b'\x89PNG\r\n\x1a\n' or png[12:16]!=b'IHDR' or struct.unpack('>II',png[16:24])!=(s['width'],s['height']):raise ValueError('visual_png_dimensions')
    if not isinstance(r['feedback'],list) or len(r['feedback'])>6:raise ValueError('visual_feedback_invalid')
    for f in r['feedback']:
        if not isinstance(f,dict) or set(f)!={'action','status'}:raise ValueError('visual_feedback_fields')
        text(f['action'],64);text(f['status'],500)


def validate_action(a,width,height):
    if not isinstance(a,dict) or set(a)!=FIELDS:raise ValueError('visual_action_fields')
    if not isinstance(a['kind'],str) or a['kind'] not in KINDS:raise ValueError('visual_action_kind')
    text(a['reason'],1000)
    unused=FIELDS-{'kind','reason'}
    def use(*keys): unused.difference_update(keys)
    if a['kind']=='click' or a['kind']=='inspect' and a['x'] is not None:
        use('x','y');integer(a['x'],0,width-1);integer(a['y'],0,height-1)
        if a['kind']=='inspect':
            use('width','height');integer(a['width'],1,width-a['x']);integer(a['height'],1,height-a['y'])
    if a['kind']=='type_text':
        use('text');text(a['text'],2000)
        if any(ord(c)<32 for c in a['text']):raise ValueError('visual_text_controls')
    if a['kind']=='key':
        use('key')
        if not isinstance(a['key'],str) or a['key'] not in KEYS:raise ValueError('visual_key')
    if a['kind']=='scroll':
        use('direction','amount')
        if not isinstance(a['direction'],str) or a['direction'] not in {'up','down'}:raise ValueError('visual_scroll')
        integer(a['amount'],1,5)
    if a['kind']=='wait':use('amount');integer(a['amount'],1,2)
    if any(a[k] is not None for k in unused):raise ValueError('visual_unused_action_fields')


def validate_response(r,request):
    if not isinstance(r,dict) or set(r)!={'version','task_id','turn','action'}:raise ValueError('visual_response_fields')
    if any(r[k]!=request[k] for k in ('version','task_id','turn')):raise ValueError('visual_response_revision_mismatch')
    validate_action(r['action'],request['screen']['width'],request['screen']['height'])
