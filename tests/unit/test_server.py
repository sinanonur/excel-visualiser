"""CORS rules, shared mode settings and serving a built frontend."""
import pytest

import app as app_module


ALLOW = 'Access-Control-Allow-Origin'


def get_health(client, origin, base_url='http://localhost:5001'):
    return client.get('/health', headers={'Origin': origin}, base_url=base_url)


@pytest.fixture(autouse=True)
def default_cors(monkeypatch):
    monkeypatch.delenv('CORS_ORIGINS', raising=False)


@pytest.mark.parametrize('origin', [
    'http://localhost:3000', 'http://127.0.0.1:8080', 'http://[::1]:3000', 'https://localhost',
])
def test_pages_on_this_computer_are_allowed(client, origin):
    assert get_health(client, origin).headers.get(ALLOW) == origin


@pytest.mark.parametrize('origin', [
    'https://evil.example', 'http://localhost.evil.example', 'http://localhost:3000.evil.example',
    'http://localhost:3000/path', 'null', 'file://', 'ftp://localhost',
])
def test_other_sites_are_refused(client, origin):
    response = get_health(client, origin)
    assert response.status_code == 200 and ALLOW not in response.headers


def test_page_from_the_same_host_is_allowed_in_shared_mode(client):
    """A page at http://office-pc:3000 reaching the API at http://office-pc:5001."""
    for host in ('office-pc', '192.168.1.20'):
        base = f'http://{host}:5001'
        assert get_health(client, f'http://{host}:3000', base).headers.get(ALLOW) == f'http://{host}:3000'
        # A different machine's page may not read this machine's data.
        assert ALLOW not in get_health(client, 'http://192.168.1.99:3000', base).headers


def test_preflight_for_json_posts(client):
    response = client.options('/plot', headers={
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type',
    })
    assert response.status_code == 200
    assert response.headers[ALLOW] == 'http://localhost:3000'
    assert 'POST' in response.headers['Access-Control-Allow-Methods']
    assert response.headers['Access-Control-Allow-Headers'] == 'content-type'


def test_error_responses_are_readable_by_the_page(client):
    response = client.post('/plot', json={}, headers={'Origin': 'http://localhost:3000'})
    assert response.status_code == 400 and response.headers.get(ALLOW) == 'http://localhost:3000'


def test_cors_origins_setting_replaces_the_default(client, monkeypatch):
    monkeypatch.setenv('CORS_ORIGINS', 'https://viz.example.org, http://intranet:8080/')
    assert get_health(client, 'https://viz.example.org').headers.get(ALLOW) == 'https://viz.example.org'
    assert get_health(client, 'http://intranet:8080').headers.get(ALLOW) == 'http://intranet:8080'
    assert ALLOW not in get_health(client, 'http://localhost:3000').headers
    monkeypatch.setenv('CORS_ORIGINS', '*')
    assert get_health(client, 'https://anything.example').headers.get(ALLOW) == '*'


# -- server settings -----------------------------------------------------------

@pytest.mark.parametrize('argv,env,expected', [
    ([], {}, ('127.0.0.1', 5001, False, False)),
    (['--shared'], {}, ('0.0.0.0', 5001, False, True)),
    ([], {'EXCEL_VISUALIZER_SHARED': '1'}, ('0.0.0.0', 5001, False, True)),
    ([], {'EXCEL_VISUALIZER_SHARED': 'no'}, ('127.0.0.1', 5001, False, False)),
    (['--shared'], {'FLASK_HOST': '192.168.1.20'}, ('192.168.1.20', 5001, False, True)),
    (['--port', '6000'], {'FLASK_PORT': '7000', 'FLASK_DEBUG': 'true'}, ('127.0.0.1', 6000, True, False)),
    ([], {'FLASK_PORT': '7000'}, ('127.0.0.1', 7000, False, False)),
])
def test_server_settings(argv, env, expected):
    settings = app_module.server_settings(argv, env)
    assert (settings['host'], settings['port'], settings['debug'], settings['shared']) == expected


# -- built frontend ------------------------------------------------------------

@pytest.fixture
def frontend_dir(tmp_path):
    (tmp_path / 'static' / 'js').mkdir(parents=True)
    (tmp_path / 'index.html').write_text('<!doctype html><html><head><title>t</title></head><body><div id="root"></div></body></html>')
    (tmp_path / 'static' / 'js' / 'main.1234.js').write_text('console.log(1)')
    (tmp_path / 'favicon.ico').write_bytes(b'\x00\x01')
    app_module.app.config['FRONTEND_DIR'] = str(tmp_path)
    yield tmp_path
    app_module.app.config['FRONTEND_DIR'] = None


def test_no_frontend_means_no_page(client):
    app_module.app.config['FRONTEND_DIR'] = None
    assert client.get('/').status_code == 404


def test_serves_the_built_frontend(client, frontend_dir):
    index = client.get('/')
    assert index.status_code == 200 and index.mimetype == 'text/html'
    html = index.get_data(as_text=True)
    assert html.startswith('<!doctype html><html><head><script>window.EXCEL_VISUALISER_API_URL')
    assert index.headers['Cache-Control'] == 'no-cache'

    script = client.get('/static/js/main.1234.js')
    assert script.status_code == 200 and script.get_data(as_text=True) == 'console.log(1)'
    assert client.get('/favicon.ico').data == b'\x00\x01'
    # Client-side routes fall back to the page; missing assets do not.
    assert 'id="root"' in client.get('/some/view').get_data(as_text=True)
    assert client.get('/static/js/missing.js').status_code == 404
    assert client.get('/../conftest.py').status_code == 404


def test_api_routes_win_over_the_page(client, frontend_dir):
    assert client.get('/health').get_json()['status'] == 'ok'
    assert client.get('/session').get_json() == {'loaded': False}
    assert client.get('/filter-options/anything').status_code == 400   # API, not the page


def test_frontend_dir_from_environment(frontend_dir, monkeypatch):
    monkeypatch.setenv('EXCEL_VISUALIZER_FRONTEND_DIR', str(frontend_dir))
    assert app_module.find_frontend_dir() == str(frontend_dir)
    monkeypatch.setenv('EXCEL_VISUALIZER_FRONTEND_DIR', str(frontend_dir / 'static'))
    assert app_module.find_frontend_dir() is None
