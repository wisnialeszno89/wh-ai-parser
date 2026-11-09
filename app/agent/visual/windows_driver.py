"""Window-scoped screenshot/input driver. No business/application routing."""
import ctypes,time
from contextlib import contextmanager
from dataclasses import dataclass
from PIL import ImageGrab,ImageChops,ImageStat
from .runtime import VisualFrame

@dataclass(frozen=True)
class FrameToken:
    hwnd:int
    pid:int
    window_box:tuple
    view_box:tuple

@contextmanager
def physical_coordinates():
    win=ctypes.WinDLL('user32',use_last_error=True)
    setter=getattr(win,'SetThreadDpiAwarenessContext',None);previous=None
    if setter:
        setter.argtypes=[ctypes.c_void_p];setter.restype=ctypes.c_void_p
        previous=setter(ctypes.c_void_p(-4))
    try:yield
    finally:
        if setter and previous:setter(previous)


def model_to_window(frame,x,y):
    l,t,r,b=frame.token.view_box
    return l+int(x*(r-l)/frame.image.width),t+int(y*(b-t)/frame.image.height)


def literal_keys(text):
    return ''.join({'{':'{{}','}':'{}}','+':'{+}','^':'{^}','%':'{%}','~':'{~}','(':'{(}',')':'{)}'}.get(c,c) for c in text)

class WindowsVisualDriver:
    def __init__(self,title,pid,*,allow_enter=False,replace_focused_text=None):
        from pywinauto import Desktop
        from ctypes import wintypes
        self.user32=ctypes.WinDLL('user32',use_last_error=True)
        self.user32.GetForegroundWindow.restype=wintypes.HWND
        self.user32.GetClientRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
        self.user32.GetClientRect.restype=wintypes.BOOL
        self.user32.ClientToScreen.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.POINT)]
        self.user32.ClientToScreen.restype=wintypes.BOOL
        self.user32.WindowFromPoint.argtypes=[wintypes.POINT]
        self.user32.WindowFromPoint.restype=wintypes.HWND
        self.user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        self.user32.GetWindowThreadProcessId.restype=wintypes.DWORD
        candidates=[w for w in Desktop(backend='win32').windows()
                    if w.window_text()==title and w.element_info.process_id==pid and w.is_visible()]
        if len(candidates)!=1:raise RuntimeError('visual_scope_not_unique')
        self.window=candidates[0];self.hwnd=int(self.window.handle);self.pid=pid;self.view=None;self.allow_enter=allow_enter
        self.replace_focused_text=replace_focused_text
        self.window.set_focus()
        if int(self.user32.GetForegroundWindow() or 0)!=self.hwnd:raise RuntimeError('visual_focus_denied')

    def _check(self):
        from ctypes import wintypes
        actual=wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(self.hwnd,ctypes.byref(actual))
        if actual.value!=self.pid or int(self.user32.GetForegroundWindow() or 0)!=self.hwnd:
            raise RuntimeError('visual_scope_or_foreground_changed')

    def _client_box(self):
        from ctypes import wintypes
        rect=wintypes.RECT()
        origin=wintypes.POINT()
        if not self.user32.GetClientRect(self.hwnd,ctypes.byref(rect)):
            raise RuntimeError('visual_client_rect_unavailable')
        if not self.user32.ClientToScreen(self.hwnd,ctypes.byref(origin)):
            raise RuntimeError('visual_client_origin_unavailable')
        return origin.x,origin.y,origin.x+rect.right,origin.y+rect.bottom

    def capture(self):
        with physical_coordinates():
            self._check();box=self._client_box()
            width,height=box[2]-box[0],box[3]-box[1]
            if width<=0 or height<=0:raise RuntimeError('visual_window_geometry_invalid')
            view=self.view or (0,0,width,height)
            if view[2]>width or view[3]>height:self.view=None;view=(0,0,width,height)
            # A view is relative to the owned window, not absolute desktop pixels.
            bounds=(box[0]+view[0],box[1]+view[1],box[0]+view[2],box[1]+view[3])
            image=ImageGrab.grab(bbox=bounds,all_screens=True).convert('RGB')
            scale=min(1600/image.width,1200/image.height,2.0 if self.view else 1.0)
            if scale!=1.0:image=image.resize((max(1,int(image.width*scale)),max(1,int(image.height*scale))))
            return VisualFrame(image,FrameToken(self.hwnd,self.pid,box,view))

    def is_fresh(self,frame,action):
        current=self.capture()
        if current.token!=frame.token or current.image.size!=frame.image.size:return False
        before,after=frame.image,current.image
        if action['kind']=='click':
            x,y=action['x'],action['y'];region=(max(0,x-18),max(0,y-18),min(before.width,x+19),min(before.height,y+19))
            before,after=before.crop(region),after.crop(region)
        delta=ImageStat.Stat(ImageChops.difference(before,after).convert('L')).mean[0]/255
        return delta<=.002

    def _owned_point(self,x,y):
        from ctypes import wintypes
        hit=self.user32.WindowFromPoint(wintypes.POINT(x,y))
        actual=wintypes.DWORD()
        if hit:self.user32.GetWindowThreadProcessId(hit,ctypes.byref(actual))
        if not hit or actual.value!=self.pid:raise RuntimeError('visual_point_not_owned_by_scope')

    def _type_text(self, text, send_keys):
        if self.replace_focused_text and self.replace_focused_text():
            self._check()
            send_keys('^a', vk_packet=False, pause=.05)
            self._check()
        send_keys(literal_keys(text), with_spaces=True, pause=.03)

    def perform(self,frame,action):
        self._check();kind=action['kind']
        from pywinauto import mouse
        from pywinauto.keyboard import send_keys
        with physical_coordinates():
            if kind=='click':
                x,y=model_to_window(frame,action['x'],action['y']);l,t,_,_=frame.token.window_box
                self._owned_point(l+x,t+y)
                mouse.click(coords=(l+x,t+y))
            elif kind=='type_text':
                self._type_text(action['text'], send_keys)
            elif kind=='key':
                keys={'CTRL+A':'^a','BACKSPACE':'{BACKSPACE}','HOME':'{HOME}','END':'{END}','TAB':'{TAB}','ESC':'{ESC}','ENTER':'{ENTER}'}
                if action['key']=='ENTER' and not self.allow_enter:raise ValueError('visual_enter_not_authorized')
                send_keys(keys[action['key']],vk_packet=False,pause=.05)
            elif kind=='scroll':
                l,t,r,b=frame.token.window_box
                self._owned_point((l+r)//2,(t+b)//2)
                mouse.scroll(coords=((l+r)//2,(t+b)//2),wheel_dist=action['amount']*(1 if action['direction']=='up' else -1))
            elif kind=='wait':time.sleep(action['amount'])
            elif kind=='inspect':
                if action['x'] is None:self.view=None
                else:
                    l,t=model_to_window(frame,action['x'],action['y'])
                    r,b=model_to_window(frame,action['x']+action['width'],action['y']+action['height'])
                    self.view=(l,t,r,b)
            else:raise ValueError('visual_input_action_unsupported')
