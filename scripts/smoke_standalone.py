#!/usr/bin/env python3
"""Smoke-test a built standalone package. Standard library only.

    python scripts/smoke_standalone.py standalone/runtime/excel-visualizer-backend/excel-visualizer-backend[.exe]

Starts the executable from another working directory, then checks that it
answers, serves the web page, loads test_data.xlsx, draws a plot, builds the
profile and exports Excel. Exits non-zero on the first failure.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get('SMOKE_PORT', '5087'))
BASE = f'http://127.0.0.1:{PORT}'


def request(path, data=None, headers=None, method=None):
    req = urllib.request.Request(BASE + path, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()


def post_json(path, payload):
    return request(path, json.dumps(payload).encode(), {'Content-Type': 'application/json'})


def upload(path):
    boundary = uuid.uuid4().hex
    with open(path, 'rb') as handle:
        content = handle.read()
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{os.path.basename(path)}"\r\n'
            'Content-Type: application/octet-stream\r\n\r\n').encode() + content + f'\r\n--{boundary}--\r\n'.encode()
    return request('/upload', body, {'Content-Type': f'multipart/form-data; boundary={boundary}'})


def check(name, condition, detail=''):
    print(f'{"PASS" if condition else "FAIL"}  {name}{"  - " + detail if detail else ""}', flush=True)
    if not condition:
        raise SystemExit(1)


def main(executable):
    executable = os.path.abspath(executable)
    check('executable exists', os.path.isfile(executable), executable)
    workdir = tempfile.mkdtemp(prefix='smoke-')
    env = dict(os.environ, FLASK_PORT=str(PORT), EXCEL_VISUALIZER_CACHE_DIR=os.path.join(workdir, 'cache'))
    log = open(os.path.join(workdir, 'server.log'), 'wb')
    process = subprocess.Popen([executable], cwd=workdir, env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.time() + 120
        status = None
        while time.time() < deadline and process.poll() is None:
            try:
                status, _, body = request('/health')
                if status == 200:
                    break
            except (urllib.error.URLError, ConnectionError, OSError):
                pass
            time.sleep(1)
        if status != 200:
            log.flush()
            with open(log.name, 'rb') as handle:
                print(handle.read()[-3000:].decode(errors='replace'))
        check('server answers /health', status == 200, f'exit code {process.poll()}' if process.poll() is not None else '')

        status, headers, body = request('/')
        html = body.decode(errors='replace')
        check('serves the web page', status == 200 and 'id="root"' in html and 'EXCEL_VISUALISER_API_URL' in html)
        script = re.search(r'/static/js/main\.[0-9a-f]+\.js', html)
        check('page references its script', bool(script))
        status, _, body = request(script.group(0))
        check('serves the page script', status == 200 and len(body) > 100_000, f'{len(body):,} bytes')

        status, _, body = upload(os.path.join(ROOT, 'test_data.xlsx'))
        loaded = json.loads(body) if status == 200 else {}
        check('loads test_data.xlsx', status == 200 and loaded.get('shape') == [5, 8], body[:200].decode(errors='replace'))

        status, _, body = post_json('/plot', {'type': 'bar', 'columns': ['Department']})
        check('draws a bar chart', status == 200 and 'plot' in json.loads(body))
        status, _, body = post_json('/plot', {'type': 'heatmap', 'columns': []})
        check('draws a correlation heatmap', status == 200)
        status, _, body = request('/profile')
        check('builds the profile', status == 200 and json.loads(body)['overview']['rows'] == 5)
        status, headers, body = request('/export?format=xlsx')
        check('exports Excel', status == 200 and body[:2] == b'PK', headers.get('Content-Disposition', ''))
        status, _, body = post_json('/generate-llm-plot', {'prompt': 'scatter', 'model': 'test'})
        check('AI plot with the offline test model', status == 200)
        check('still a single running server', process.poll() is None)
    finally:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
        log.close()
    print('Standalone smoke test passed')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
