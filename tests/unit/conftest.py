import os
import sys
import tempfile
from io import BytesIO

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'backend'))

# Keep the type-override cache out of the real temp directory.
os.environ['EXCEL_VISUALIZER_CACHE_DIR'] = tempfile.mkdtemp(prefix='excel_vis_test_cache_')

import app as app_module  # noqa: E402


def make_frame(rows=40):
    """A dataset covering every column type plus the awkward cases."""
    departments = ['IT', 'HR', 'Finance', 'Ops']
    return pd.DataFrame({
        'Name': [f'Person {i}' for i in range(rows)],
        'Age': [22 + (i * 7) % 30 for i in range(rows)],
        'Salary': [30000 + ((i * 7) % 30) * 1500 + (i % 3) * 100 for i in range(rows)],
        'Department': [departments[i % 4] for i in range(rows)],
        'Active': [i % 3 != 0 for i in range(rows)],
        'Hired': pd.date_range('2020-01-01', periods=rows, freq='15D'),
        'Skills': ['[Python, SQL]' if i % 2 else '[Excel]' for i in range(rows)],
        'Tags': ["{'a', 'b'}" if i % 2 else "{'a'}" for i in range(rows)],
        'Score': [None if i % 10 == 0 else float(i) for i in range(rows)],
        'Level': [(i % 3) + 1 for i in range(rows)],
        'Price': ['26,6,' if i == 5 else str(10 + i) for i in range(rows)],
    })


def to_xlsx(sheets):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def isolated_type_cache(tmp_path, monkeypatch):
    """Fresh override cache per test.

    Uploading the same bytes twice restores remembered column types (that is
    the feature), so a shared cache would make tests depend on their order.
    """
    monkeypatch.setenv('EXCEL_VISUALIZER_CACHE_DIR', str(tmp_path / 'type_cache'))


@pytest.fixture
def frame():
    return make_frame()


@pytest.fixture
def client():
    app_module.app.testing = True
    app_module.data_processor.reset()
    with app_module.app.test_client() as test_client:
        yield test_client
    app_module.data_processor.reset()


@pytest.fixture
def processor():
    return app_module.data_processor


def upload(client, content, filename='data.xlsx', **form):
    return client.post('/upload', data={'file': (BytesIO(content), filename), **form},
                       content_type='multipart/form-data')


@pytest.fixture
def loaded(client, frame):
    """Client with the standard dataset already uploaded."""
    response = upload(client, to_xlsx({'Main': frame}))
    assert response.status_code == 200, response.get_json()
    return client
