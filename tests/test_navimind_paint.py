import copy
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from tools.navimind_paint import DesktopWithPaint,geometry,render,validate_paint_task,verify_image

TASK=dict(kind='draw_window_in_paint',folder='Rysunki',file_name='okno-test.png',width_mm=1500,height_mm=1400,construction='double_fixed',frame_color='antracyt')
class Tables:
    def __init__(self,root):self.root=root;self.results={};self.calls=0
    def status(self):return dict(status='ready',capabilities=['create_window_table'],currentTable={'file':'existing-table'})
    def execute(self,body):self.calls+=1;return {'table':True}
class Launcher:
    def __init__(self,fail=False,change=False):self.calls=0;self.fail=fail;self.change=change
    def open(self,path,trace):
        self.calls+=1
        if self.fail:raise RuntimeError('Okno Painta niepotwierdzone.')
        if self.change:Image.new('RGB',(720,480),'red').save(path)
        return {'open_status':'verified','paint_pid':123,'paint_hwnd':456}
class PaintTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.tables=Tables(self.root);self.launch=Launcher();self.agent=DesktopWithPaint(self.tables,self.launch)
    def tearDown(self):self.tmp.cleanup()
    def job(self,task=None,id='paint-job-12345678'):return dict(id=id,task=copy.deepcopy(task or TASK),expectedRevision=None)
    def test_opposite_handles_and_directions_for_all_layouts(self):
        for layout,directions in [('single_dkl',['LEFT']),('single_dkr',['RIGHT']),('double_fixed',['LEFT','RIGHT'])]:
            task={**TASK,'construction':layout};g=geometry(task)
            self.assertEqual([f['hinge_side'] for f in g['fields']],directions)
            for f in g['fields']:self.assertNotEqual(f['hinge_side'],f['handle_side'])
            l,t,r,b=g['outer'];self.assertAlmostEqual((r-l)/(b-t),1500/1400,delta=.01)
            for f in g['fields']:
                a,c,d,e=f['box'];self.assertTrue(l<a<d<r and t<c<e<b)
    def test_variants_render_and_read_back_pixels(self):
        for layout in ['single_dkl','single_dkr','double_fixed']:
            for color in ['bialy','antracyt','mahon']:
                image,_=render({**TASK,'construction':layout,'frame_color':color})
                path=self.root/(layout+'-'+color+'.png');image.save(path);verify_image(path,image)
                self.assertEqual(image.size,(720,480));self.assertNotEqual(image.getbbox(),None)
        image,_=render(TASK);path=self.root/'corrupt.png';Image.new('RGB',(720,480),'red').save(path)
        with self.assertRaises(ValueError):verify_image(path,image)
    def test_create_is_idempotent_and_keeps_active_table(self):
        before=self.agent.status()['currentTable'];body=self.job();r=self.agent.execute(body)
        self.assertEqual(r['status'],'verified');self.assertTrue(Path(r['file']).exists())
        self.assertEqual(self.agent.execute(body),r);self.assertEqual(self.launch.calls,1)
        self.assertEqual(self.agent.status()['currentTable'],before)
        changed=self.job({**TASK,'width_mm':1600});self.assertEqual(self.agent.execute(changed)['status'],'review');self.assertEqual(self.launch.calls,1)
        self.assertEqual(self.agent.execute(body),r)
    def test_existing_image_is_preserved_and_new_suffix_returned(self):
        folder=self.root/'Rysunki';folder.mkdir();old=folder/'okno-test.png';old.write_bytes(b'previous-user-image')
        r=self.agent.execute(self.job());self.assertEqual(r['status'],'verified');self.assertEqual(Path(r['file']).name,'okno-test-2.png');self.assertEqual(old.read_bytes(),b'previous-user-image')
        metadata=json.loads(Path(r['file']+'.json').read_text());self.assertEqual(metadata['task']['width_mm'],1500)
    def test_unconfirmed_window_is_review_with_the_preserved_image(self):
        self.agent=DesktopWithPaint(self.tables,Launcher(fail=True));body=self.job();r=self.agent.execute(body)
        self.assertEqual(r['status'],'review');self.assertTrue(Path(r['file']).exists());self.assertEqual(self.agent.execute(body),r);self.assertEqual(self.agent.launcher.calls,1)
    def test_external_change_during_opening_is_detected(self):
        self.agent=DesktopWithPaint(self.tables,Launcher(change=True));self.assertEqual(self.agent.execute(self.job())['status'],'review')
    def test_invalid_layout_color_numbers_and_paths_are_rejected(self):
        for key,value in [('construction','hst'),('frame_color','RAL9007'),('width_mm',True),('height_mm',99),('width_mm',10001),('folder','../outside'),('file_name','image.exe'),('folder','CON'),('file_name','../file.png'),('width_mm',100)]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate_paint_task({**TASK,key:value})
        with self.assertRaises(ValueError):validate_paint_task({**TASK,'script':'anything'})
    def test_symlinks_are_not_followed(self):
        outside=self.root/'outside';outside.mkdir();(self.root/'Rysunki').symlink_to(outside,target_is_directory=True)
        r=self.agent.execute(self.job());self.assertEqual(r['status'],'review');self.assertEqual(list(outside.iterdir()),[])
    def test_table_requests_are_delegated(self):
        self.assertEqual(self.agent.execute({'task':{'kind':'create_window_table'}}),{'table':True});self.assertEqual(self.tables.calls,1)

if __name__=='__main__':unittest.main()
