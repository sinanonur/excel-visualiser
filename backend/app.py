"""Flask API for the Excel Data Science Visualizer.

The server is single-user and stateful: one ``DataProcessor`` holds the loaded
dataset in memory. A lock serialises requests because the development server
is threaded and several endpoints mutate that shared state.
"""

import builtins
import functools
import hashlib
import json
import os
import sys
import threading
import traceback
from io import BytesIO

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objs as go
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from llm import GeminiLlm, TestLlm
from plots import PlotError, figure_to_json
from processing import (  # noqa: F401  (re-exported for existing importers)
    SUPPORTED_EXTENSIONS,
    DataError,
    DataProcessor,
    convert_to_json_serializable,
    to_jsonable,
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_UPLOAD_MB', '200')) * 1024 * 1024
# Keep keys in insertion order so column_info lists columns as they appear in the file.
app.json.sort_keys = False


def _cors_origins():
    """Origins allowed to read API responses.

    The dataset is private to the machine, so by default only pages served
    from localhost may call the API. Set CORS_ORIGINS (comma separated, or
    ``*``) when the frontend is served from another host.
    """
    configured = os.environ.get('CORS_ORIGINS', '').strip()
    if configured == '*':
        return '*'
    if configured:
        return [origin.strip() for origin in configured.split(',') if origin.strip()]
    return [r'^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$']


CORS(app, origins=_cors_origins(), expose_headers=['Content-Disposition'])

data_processor = DataProcessor()
_state_lock = threading.RLock()


def locked(view):
    """Serialise access to the shared DataProcessor."""
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        with _state_lock:
            return view(*args, **kwargs)
    return wrapper


def needs_data(view):
    """Serialise access and reject the request if no dataset is loaded."""
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        with _state_lock:
            if data_processor.data is None:
                return jsonify({'error': 'No data loaded'}), 400
            return view(*args, **kwargs)
    return wrapper


def _body():
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def _unfiltered():
    """The unfiltered frame (callers that set ``data`` directly may leave it unset)."""
    return data_processor.original_data if data_processor.original_data is not None else data_processor.data


@app.errorhandler(DataError)
def handle_data_error(error):
    return jsonify({'error': str(error)}), 400


@app.errorhandler(PlotError)
def handle_plot_error(error):
    return jsonify({'error': str(error)}), 400


@app.errorhandler(413)
def handle_too_large(_error):
    limit_mb = app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
    return jsonify({'error': f'File is too large (limit {limit_mb} MB)'}), 413


# ---------------------------------------------------------------------------
# Health / session
# ---------------------------------------------------------------------------

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'data_loaded': data_processor.data is not None})


@app.route('/session', methods=['GET'])
@locked
def get_session():
    """Current dataset state, so a reloaded page can pick up where it left off."""
    if data_processor.data is None or data_processor.original_data is None:
        return jsonify({'loaded': False})
    return jsonify(to_jsonable({'loaded': True, **data_processor.state()}))


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

@app.route('/upload', methods=['POST'])
@locked
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.lower().endswith(SUPPORTED_EXTENSIONS):
        return jsonify({'error': 'Unsupported file type. Upload .xlsx, .xls, .xlsm, .csv or .tsv'}), 400

    file_content = file.read()
    if not file_content:
        return jsonify({'error': 'The file is empty'}), 400

    data_processor.load_file(file_content, file.filename, sheet=request.form.get('sheet') or None)
    data_processor.file_hash = hashlib.sha256(file_content).hexdigest()
    data_processor.restore_overrides()

    response = {
        'success': True,
        **data_processor.state(),
        'preview': data_processor.get_page(1, 10)['data'],
    }
    return jsonify(to_jsonable(response))


@app.route('/select-sheet', methods=['POST'])
@needs_data
def select_sheet():
    sheet = _body().get('sheet')
    if not sheet:
        return jsonify({'error': 'Sheet name required'}), 400
    data_processor.select_sheet(sheet)
    return jsonify(to_jsonable({'success': True, **data_processor.state()}))


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------

@app.route('/column-info', methods=['GET'])
@needs_data
def get_column_info():
    return jsonify(to_jsonable({
        'columns': list(data_processor.data.columns),
        'column_info': data_processor.column_info,
    }))


@app.route('/update-column-type', methods=['POST'])
@needs_data
def update_column_type():
    body = _body()
    column, new_type = body.get('column'), body.get('type')
    if not column or not new_type:
        return jsonify({'error': 'Column and type required'}), 400

    result = data_processor.set_column_type(column, new_type)
    return jsonify(to_jsonable({'success': True, **result, **data_processor.state()}))


@app.route('/expand-column', methods=['POST'])
@needs_data
def expand_column():
    body = _body()
    column = body.get('column')
    if not column:
        return jsonify({'error': 'Column required'}), 400

    new_columns = data_processor.expand_list_column(column, mode=body.get('mode') or 'positional')
    return jsonify(to_jsonable({'success': True, 'new_columns': new_columns, **data_processor.state()}))


# ---------------------------------------------------------------------------
# Preview / profile / export
# ---------------------------------------------------------------------------

@app.route('/data-preview', methods=['GET'])
@needs_data
def get_data_preview():
    page = data_processor.get_page(
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 50, type=int),
        sort_by=request.args.get('sort_by') or None,
        sort_dir=request.args.get('sort_dir', 'asc'),
        search=request.args.get('search') or None,
    )
    return jsonify(page)


@app.route('/profile', methods=['GET'])
@needs_data
def get_profile():
    return jsonify(to_jsonable(data_processor.profile()))


@app.route('/export', methods=['GET'])
@needs_data
def export_data():
    payload, filename, mimetype = data_processor.export(
        file_format=request.args.get('format', 'csv').lower(),
        scope=request.args.get('scope', 'filtered').lower(),
    )
    return send_file(BytesIO(payload), mimetype=mimetype, as_attachment=True, download_name=filename)


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def _filter_options_response(column):
    if not column:
        return jsonify({'error': 'Column required'}), 400
    options = data_processor.get_filter_options(column)
    if options is None:
        return jsonify({'error': f'No filter available for column "{column}"'}), 404
    return jsonify(to_jsonable(options))


@app.route('/filter-options', methods=['GET'])
@needs_data
def get_filter_options_by_query():
    """Preferred form: ``/filter-options?column=<name>`` works for any column name."""
    return _filter_options_response(request.args.get('column'))


@app.route('/filter-options/<path:column>', methods=['GET'])
@needs_data
def get_filter_options(column):
    return _filter_options_response(column)


@app.route('/apply-filters', methods=['POST'])
@needs_data
def apply_filters():
    data_processor.apply_filters(_body().get('filters', {}))
    return jsonify(to_jsonable({'success': True, **data_processor.filter_status()}))


@app.route('/clear-filters', methods=['POST'])
@needs_data
def clear_filters():
    data_processor.clear_filters()
    return jsonify(to_jsonable({'success': True, **data_processor.filter_status()}))


@app.route('/filter-status', methods=['GET'])
@needs_data
def get_filter_status():
    return jsonify(to_jsonable({
        'has_filters': len(data_processor.active_filters) > 0,
        'active_filters': data_processor.active_filters,
        'filtered_rows': len(data_processor.data),
        'total_rows': len(_unfiltered()),
    }))


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

@app.route('/plot', methods=['POST'])
@needs_data
def generate_plot():
    try:
        fig = data_processor.build_figure(_body())
    except PlotError:
        raise
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': f'Could not generate plot: {exc}'}), 500
    return jsonify({'plot': figure_to_json(fig)})


# Modules LLM-generated plot code may import. This narrows what a bad
# response can do by accident; it is NOT a security sandbox (pandas itself can
# read and write files), so only enable AI plots for models you trust.
_LLM_ALLOWED_MODULES = {
    'plotly', 'pandas', 'numpy', 'math', 'statistics', 'datetime', 'json', 're',
    'collections', 'itertools', 'functools', 'scipy', 'sklearn',
}
_LLM_BLOCKED_BUILTINS = {
    'open', 'exec', 'eval', 'compile', 'input', 'breakpoint', 'exit', 'quit', 'help',
}


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level != 0 or name.split('.')[0] not in _LLM_ALLOWED_MODULES:
        raise ImportError(f'Import of "{name}" is not allowed in generated plot code')
    return builtins.__import__(name, globals, locals, fromlist, level)


def safe_exec(code, local_vars):
    """Run generated plot code with a reduced set of builtins and imports."""
    safe_builtins = {name: value for name, value in vars(builtins).items()
                     if name not in _LLM_BLOCKED_BUILTINS}
    safe_builtins['__import__'] = _restricted_import
    scope = {'__builtins__': safe_builtins, 'go': go, 'px': px, 'pd': pd, 'np': np,
             'json': json, 'plotly': plotly}
    # One namespace for globals and locals so functions and comprehensions
    # defined by the generated code can see ``df`` and each other.
    scope.update(local_vars)
    try:
        exec(code, scope)
    except Exception as exc:
        print(f'Error executing plot code: {type(exc).__name__}: {exc}')
        for number, line in enumerate(code.split('\n'), 1):
            print(f'{number:3}: {line}')
        traceback.print_exc()
        raise
    local_vars.update({key: value for key, value in scope.items() if key != '__builtins__'})


@app.route('/generate-llm-plot', methods=['POST'])
@needs_data
def generate_llm_plot():
    config = _body()
    prompt = config.get('prompt')
    selected_columns = config.get('columns')
    model = config.get('model', 'gemini')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    plot_code = None
    try:
        llm = TestLlm() if model == 'test' else GeminiLlm()
        plot_code = llm.generate_plot_code(prompt, data_processor.data, selected_columns)

        if not plot_code or len(plot_code.strip()) < 10:
            return jsonify({'error': 'LLM generated empty or too short code',
                            'generated_code': plot_code}), 500

        # A copy, so generated code cannot alter the loaded dataset.
        local_vars = {'df': data_processor.data.copy(), 'fig': None}
        safe_exec(plot_code, local_vars)
        fig = local_vars.get('fig')
        if fig is None:
            return jsonify({'error': 'The generated code did not create a "fig" object',
                            'generated_code': plot_code}), 500
        return jsonify({'plot': figure_to_json(fig), 'generated_code': plot_code})

    except Exception as exc:
        print(f'LLM plot error: {exc}')
        return jsonify({
            'error': f'Error generating plot: {exc}',
            'generated_code': plot_code,
            'model': model,
            'selected_columns': selected_columns,
            'available_columns': list(data_processor.data.columns),
        }), 500


if __name__ == '__main__':
    # Local-only by default: the API exposes the loaded dataset and runs
    # generated code, so it must not listen on the network unless asked to
    # (Docker sets FLASK_HOST=0.0.0.0). FLASK_DEBUG=1 enables the reloader
    # and debugger for development.
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', '5001'))
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    app.run(host=host, port=port, debug=debug)
