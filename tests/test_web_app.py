import subprocess
import sys
import time
from pathlib import Path

import pytest
pytest.importorskip("streamlit")

def test_streamlit_app_starts(tmp_path):
    script = Path('ui/web_app.py')
    log = tmp_path / 'out.txt'
    with log.open('w') as log_file:
        proc = subprocess.Popen(
            [
                sys.executable,
                '-m',
                'streamlit',
                'run',
                str(script),
                '--server.headless',
                'true',
                '--server.port',
                '0',
            ],
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        try:
            time.sleep(5)
        finally:
            proc.terminate()
            proc.wait(timeout=10)
    output = log.read_text(encoding='utf-8')
    assert 'Streamlit app' in output or 'You can now view' in output

