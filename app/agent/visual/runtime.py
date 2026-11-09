"""Goal -> screenshot -> one action -> screenshot; no app-specific steps."""
import base64,io,json,hashlib
from uuid import uuid4
from dataclasses import dataclass
from PIL import ImageChops
from .contract import validate_request,validate_response

@dataclass
class VisualFrame:
    image:object
    token:object  # local scope/geometry; never sent to model

    def screen(self):
        buf=io.BytesIO();self.image.convert('RGB').save(buf,format='PNG')
        return {'image_data_url':'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode('ascii'),
                'width':self.image.width,'height':self.image.height}


def image_change(before,after):
    """Approximate visible change; cursor blink alone is not task progress."""
    if before.size!=after.size:return 1.0
    delta=ImageChops.difference(before.convert('RGB'),after.convert('RGB'))
    channels=delta.split()
    strongest=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
    hist=strongest.histogram()
    return sum(hist[25:])/(before.width*before.height)

def action_memory(action):
    # Preserve the actual target/edit in bounded feedback, not just 'click'.
    fields={key:action[key] for key in ('kind','x','y','width','height','text','key','direction','amount') if action[key] is not None}
    if 'text' in fields:fields['text']=fields['text'][:80]
    return json.dumps(fields,ensure_ascii=False,separators=(',',':'))[:240]

def run_visual_task(driver,reasoner,goal,*,execute=False,max_steps=12,verify=None,trace=None):
    if type(max_steps) is not int or not 1<=max_steps<=30:raise ValueError('visual_step_budget')
    task_id='visual-'+uuid4().hex
    history=[];repeats={};model_calls=0;input_actions=0;input_attempts=0;tool_failures=0
    pending=None;ineffective_clicks=0;last_ineffective_click=None;recent_clicks=[];blocked_revisits=0
    for turn in range(max_steps):
        frame=driver.capture()
        if trace:trace(turn,frame,None)
        if pending is not None:
            old_frame,old_action=pending;pending=None
            same_view=old_frame.token==frame.token and old_frame.image.size==frame.image.size
            change=image_change(old_frame.image,frame.image) if same_view else 1.0
            print(f'VISUAL_CHANGED_PIXEL_RATIO={change:.6f}')
            no_visible_change=same_view and change<.0005
            if old_action['kind']=='inspect':
                status = (
                    'Screenshot is cropped. Coordinates are relative to the current image. '
                    'Use inspect with null bounds to return to the full window before working outside this crop.'
                    if old_action['x'] is not None else 'Full-window screenshot requested.'
                )
            elif no_visible_change:
                status = (
                    'No substantial image change detected (small focus/caret changes may be missed). '
                    'If the input is focused, type instead of clicking it again. '
                    'If cropped, return to the full window with inspect and null bounds.'
                )
            else:
                status = 'Image changed; inspect CURRENT screenshot to verify the actual effect. Change alone is not goal completion.'
            history.append({'action':old_action['kind'],'status':action_memory(old_action)+'; '+status})
            if old_action['kind']=='click' and no_visible_change:
                ineffective_clicks+=1
                last_ineffective_click=(frame.token,frame.image.size,old_action['x'],old_action['y'])
            else:
                ineffective_clicks=0;last_ineffective_click=None
            if ineffective_clicks>=3:
                print('VISUAL_RESULT=clicks_without_visible_effect');return 'review'
        request={'version':'visual-1','task_id':task_id,'turn':turn,'goal':goal,'screen':frame.screen(),'feedback':history[-6:]}
        validate_request(request)
        response=reasoner.reason(request);model_calls+=1
        validate_response(response,request)
        action=response['action'];kind=action['kind']
        if trace:trace(turn,frame,action)
        print(f'VISUAL_TURN={turn} ACTION={kind} MODEL_CALLS={model_calls} INPUT_ACTIONS={input_actions} INPUT_ATTEMPTS={input_attempts}')
        if kind=='click':print(f"VISUAL_CLICK_IMAGE_POINT=({action['x']},{action['y']})")
        if kind=='key':print('VISUAL_KEY='+action['key'])
        if kind=='ask_user':
            print('VISUAL_ASK_USER='+action['reason']);return 'review'
        if kind=='done':
            proof=verify() if verify else None
            if proof is True:
                print('VISUAL_RESULT=verified');return 'verified'
            if proof is None:
                print('VISUAL_RESULT=completion_requires_independent_review');return 'review'
            history.append({'action':'done','status':'Local verifier rejected completion; inspect actual field values and correct the result.'})
            if sum(h['action']=='done' for h in history)>=3:return 'review'
            continue
        if not execute:
            print('VISUAL_RESULT=proposed INPUT_EXECUTED=False');return 'proposed'
        if kind=='click' and last_ineffective_click is not None:
            token,size,x,y=last_ineffective_click
            if token==frame.token and size==frame.image.size and (action['x']-x)**2+(action['y']-y)**2<=24**2:
                history.append({'action':'click','status':action_memory(action)+'; BLOCKED: nearby click already had no substantial visible effect. Use another action, inspect or ask_user.'})
                print('VISUAL_CLICK_BLOCKED=nearby_target_without_effect')
                ineffective_clicks+=1
                if ineffective_clicks>=3:return 'review'
                continue
        if kind=='click' and any(
            old.token==frame.token and old.image.size==frame.image.size
            and (action['x']-previous['x'])**2+(action['y']-previous['y'])**2<=24**2
            and image_change(old.image,frame.image)<.0005
            for old,previous in recent_clicks[-6:]
        ):
            blocked_revisits+=1
            history.append({'action':'click','status':action_memory(action)+'; BLOCKED: a nearby click was already tried from a visually equivalent screen. Do not toggle or retry this cycle; choose another action or ask_user.'})
            print('VISUAL_CLICK_BLOCKED=revisited_visual_state')
            if blocked_revisits>=2:return 'review'
            continue
        # Only dispatch attempts reserve a signature. A stale screenshot
        # has sent no input and must not prevent a fresh retry.
        signature=(hashlib.sha256(frame.image.tobytes()).hexdigest(),json.dumps({k:v for k,v in action.items() if k!='reason'},sort_keys=True))
        if kind not in {'inspect','wait'} and signature in repeats:
            repeats[signature]+=1
            history.append({'action':kind,'status':'Identical action on unchanged image blocked. Choose another strategy or ask_user.'})
            print('VISUAL_ACTION_BLOCKED=duplicate_attempt')
            if repeats[signature]>=3:return 'review'
            continue
        if not driver.is_fresh(frame,action):
            print('VISUAL_ACTION_BLOCKED=stale_frame')
            history.append({'action':kind,'status':action_memory(action)+'; Screen or active window changed while planning. No input was attempted. Reassess the next screenshot.'})
            continue
        if kind not in {'inspect','wait'}:
            repeats[signature]=1
        if kind not in {'inspect','wait'}:input_attempts+=1
        try:
            driver.perform(frame,action)
        except (ValueError,RuntimeError,OSError):
            tool_failures+=1
            print('VISUAL_TOOL_RESULT=uncertain INPUT_ATTEMPTS='+str(input_attempts))
            history.append({'action':kind,'status':action_memory(action)+'; Driver could not confirm this action. It MAY have partially executed. Inspect the next screenshot and reassess; do not blindly replay.'})
            if tool_failures>=3:return 'review'
            continue
        if kind not in {'inspect','wait'}:input_actions+=1
        if kind=='click':recent_clicks.append((frame,action));recent_clicks=recent_clicks[-6:]
        pending=(frame,action)
    print('VISUAL_RESULT=step_budget_exhausted');return 'review'
