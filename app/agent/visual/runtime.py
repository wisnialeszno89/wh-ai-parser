"""Goal -> screenshot -> one action -> screenshot; no app-specific steps."""
import base64,io,json,hashlib
from uuid import uuid4
from dataclasses import dataclass
from .contract import validate_request,validate_response

@dataclass
class VisualFrame:
    image:object
    token:object  # local scope/geometry; never sent to model

    def screen(self):
        buf=io.BytesIO();self.image.convert('RGB').save(buf,format='PNG')
        return {'image_data_url':'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode('ascii'),
                'width':self.image.width,'height':self.image.height}


def run_visual_task(driver,reasoner,goal,*,execute=False,max_steps=12,verify=None):
    if type(max_steps) is not int or not 1<=max_steps<=30:raise ValueError('visual_step_budget')
    task_id='visual-'+uuid4().hex
    history=[];repeats={};model_calls=0;input_actions=0;input_attempts=0;tool_failures=0
    for turn in range(max_steps):
        frame=driver.capture()
        request={'version':'visual-1','task_id':task_id,'turn':turn,'goal':goal,'screen':frame.screen(),'feedback':history[-6:]}
        validate_request(request)
        response=reasoner.reason(request);model_calls+=1
        validate_response(response,request)
        action=response['action'];kind=action['kind']
        print(f'VISUAL_TURN={turn} ACTION={kind} MODEL_CALLS={model_calls} INPUT_ACTIONS={input_actions} INPUT_ATTEMPTS={input_attempts}')
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
        # Compare screenshot and intended action. A repeat without changed
        # evidence requests a different strategy, not another blind dispatch.
        signature=(hashlib.sha256(frame.image.tobytes()).hexdigest(),json.dumps({k:v for k,v in action.items() if k!='reason'},sort_keys=True))
        repeats[signature]=repeats.get(signature,0)+1
        if repeats[signature]>1 and kind not in {'inspect','wait'}:
            history.append({'action':kind,'status':'Identical action on unchanged image blocked. Choose another strategy or ask_user.'})
            if repeats[signature]>=3:return 'review'
            continue
        if not driver.is_fresh(frame,action):
            history.append({'action':kind,'status':'Screen or active window changed while planning; no input executed. Reassess the next screenshot.'})
            continue
        if kind not in {'inspect','wait'}:input_attempts+=1
        try:
            driver.perform(frame,action)
        except (ValueError,RuntimeError,OSError):
            tool_failures+=1
            print('VISUAL_TOOL_RESULT=uncertain INPUT_ATTEMPTS='+str(input_attempts))
            history.append({'action':kind,'status':'Driver could not confirm this action. It MAY have partially executed. Inspect the next screenshot and reassess; do not blindly replay.'})
            if tool_failures>=3:return 'review'
            continue
        if kind not in {'inspect','wait'}:input_actions+=1
        history.append({'action':kind,'status':'Input dispatched. Inspect the NEXT screenshot to determine its real effect; do not assume success.'})
    print('VISUAL_RESULT=step_budget_exhausted');return 'review'
