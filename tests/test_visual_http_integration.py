"""Python PNG -> real HTTP -> TS validator/route -> mocked OpenAI image input."""
import os,shutil,subprocess
from pathlib import Path
import pytest
from PIL import Image
from app.agent.visual.client import VisualReasoner
from app.agent.visual.runtime import VisualFrame


def test_python_image_reaches_server_image_content_over_http():
    server=Path(os.getenv('NAVIMIND_TEST_REPO',str(Path(__file__).resolve().parents[2]/'navimind')))
    harness=server/'tests/visual-task-local-server.cjs'
    if not harness.exists() or not (server/'node_modules/typescript').exists() or not shutil.which('node'):
        pytest.skip('Local TS integration requires adjacent navimind checkout with npm dependencies.')
    process=subprocess.Popen(['node',str(harness)],cwd=server,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        # Harness startup has no network/provider access. Limit total test
        # runtime with communicate timeout on failures; server is always killed.
        import threading,queue
        ready=queue.Queue()
        threading.Thread(target=lambda:ready.put(process.stdout.readline()),daemon=True).start()
        try:line=ready.get(timeout=15).strip()
        except queue.Empty:raise AssertionError('Local visual server did not start')
        assert line.startswith('VISUAL_TEST_PORT=')
        port=int(line.split('=',1)[1])
        request=dict(version='visual-1',task_id='http-image-test',turn=0,goal='Inspect synthetic test image',screen=VisualFrame(Image.new('RGB',(200,100),'white'),None).screen(),feedback=[])
        url=f'http://127.0.0.1:{port}/api/agent/visual-task'
        response=VisualReasoner(url,'synthetic-loopback-secret').reason(request)
        assert response['action']['kind']=='inspect'
        with pytest.raises(RuntimeError,match='visual_http_401'):
            VisualReasoner(url,'wrong-synthetic-secret').reason(request)
    finally:
        process.terminate()
        try:process.communicate(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.communicate(timeout=5)
