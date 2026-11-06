"""Image transport; credentials never follow cross-origin redirects."""
import json,os
from http.cookiejar import CookieJar
from urllib.request import Request,build_opener,HTTPCookieProcessor,HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import urlsplit,parse_qs
from .contract import validate_request,validate_response


def origin(url):
    p=urlsplit(url)
    return p.scheme,p.hostname,p.port or (443 if p.scheme=='https' else 80)

class SameOriginRedirects(HTTPRedirectHandler):
    def __init__(self,url):self.allowed_origin=origin(url)
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if origin(newurl)!=self.allowed_origin:
            raise HTTPError(req.full_url,403,'visual_cross_origin_redirect_blocked',headers,fp)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class VisualReasoner:
    def __init__(self,url=None,secret=None,opener=None,access_url=None):
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
        self.access_url=access_url if access_url is not None else os.getenv('NAVIMIND_VISUAL_ACCESS_URL','').strip()
        if self.access_url:
            access=urlsplit(self.access_url)
            query=parse_qs(access.query,keep_blank_values=True)
            if (origin(self.access_url)!=origin(self.url) or access.username or access.password or access.fragment
                    or access.path not in ('','/') or set(query)!={'_vercel_share'}
                    or len(query['_vercel_share'])!=1 or not query['_vercel_share'][0]):
                raise ValueError('visual_access_url_must_be_same_origin_temporary_share_link')
        self.opener=opener or build_opener(SameOriginRedirects(self.url),HTTPCookieProcessor(CookieJar())).open
        self.access_ready=False

    def _ensure_access(self):
        if self.access_url and not self.access_ready:
            # Establish the short-lived Vercel cookie without sending the
            # application secret to the share-link GET or another origin.
            try:
                with self.opener(Request(self.access_url,method='GET'),timeout=30) as response:response.read(1024)
            except HTTPError as exc:raise RuntimeError('visual_access_http_'+str(exc.code)) from None
            except Exception:raise RuntimeError('visual_access_bootstrap_failed') from None
            self.access_ready=True

    def probe(self):
        """Invalid empty task checks auth/route only; never invokes a model."""
        self._ensure_access()
        req=Request(self.url,data=b'{}',headers={'Content-Type':'application/json','x-navimind-agent-secret':self.secret},method='POST')
        try:
            with self.opener(req,timeout=30) as response:
                status=response.status;raw=response.read(4097)
        except HTTPError as exc:
            status=exc.code;raw=exc.read(4097)
        except Exception:raise RuntimeError('visual_probe_transport_failed') from None
        try:code=json.loads(raw.decode()).get('error')
        except (ValueError,AttributeError):code=None
        if status==400 and code=='INVALID_VISUAL_TASK':return 'ready'
        if status==401 and code=='UNAUTHORIZED':return 'application_secret_rejected'
        if status==401:return 'preview_access_rejected'
        if code in {'VISUAL_NOT_ENABLED','AGENT_AUTH_NOT_CONFIGURED','AGENT_PROVIDER_NOT_CONFIGURED'}:return code.lower()
        return 'unexpected_http_'+str(status)

    def reason(self,request):
        validate_request(request)
        body=json.dumps(request,ensure_ascii=False).encode()
        if len(body)>3*1024*1024:raise ValueError('visual_payload_too_large')
        self._ensure_access()
        req=Request(self.url,data=body,headers={'Content-Type':'application/json','x-navimind-agent-secret':self.secret},method='POST')
        try:
            with self.opener(req,timeout=45) as response:raw=response.read(32769)
        except HTTPError as exc:raise RuntimeError('visual_http_'+str(exc.code)) from None
        except Exception:raise RuntimeError('visual_transport_failed') from None
        if len(raw)>32768:raise ValueError('visual_response_too_large')
        result=json.loads(raw.decode());validate_response(result,request);return result
