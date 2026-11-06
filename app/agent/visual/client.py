"""Image transport; never log payloads, headers or provider responses."""
import json,os
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
from .contract import validate_request,validate_response
class VisualReasoner:
    def __init__(self,url=None,secret=None,opener=urlopen):
        from dotenv import load_dotenv
        load_dotenv()
        self.url=url or os.getenv('NAVIMIND_VISUAL_URL','').strip()
        self.secret=secret or os.getenv('NAVIMIND_AGENT_V2_SECRET') or os.getenv('NAVIMIND_AGENT_SECRET')
        parsed=urlsplit(self.url)
        if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path!='/api/agent/visual-task'
                or not (parsed.scheme=='https' or parsed.scheme=='http' and parsed.hostname in {'localhost','127.0.0.1'})):
            raise ValueError('Set NAVIMIND_VISUAL_URL to the reviewed visual-task endpoint; no automatic route guessing.')
        if not self.secret:raise ValueError('visual_auth_missing')
        self.opener=opener
    def reason(self,request):
        validate_request(request)
        body=json.dumps(request,ensure_ascii=False).encode()
        if len(body)>3*1024*1024:raise ValueError('visual_payload_too_large')
        req=Request(self.url,data=body,headers={'Content-Type':'application/json','x-navimind-agent-secret':self.secret},method='POST')
        try:
            with self.opener(req,timeout=45) as response:raw=response.read(32769)
        except HTTPError as exc:raise RuntimeError('visual_http_'+str(exc.code)) from None
        except Exception:raise RuntimeError('visual_transport_failed') from None
        if len(raw)>32768:raise ValueError('visual_response_too_large')
        result=json.loads(raw.decode());validate_response(result,request);return result
