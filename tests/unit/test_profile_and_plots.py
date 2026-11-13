import json

import pandas as pd
import pytest

from conftest import to_xlsx, upload


def plot(client, **config):
    return client.post('/plot', json=config)


def figure(client, **config):
    response = plot(client, **config)
    assert response.status_code == 200, response.get_json()
    return json.loads(response.get_json()['plot'])


# -- profile -----------------------------------------------------------------

def test_profile_overview_and_columns(loaded):
    profile = loaded.get('/profile').get_json()
    overview = profile['overview']
    assert overview['rows'] == 40 and overview['total_rows'] == 40 and overview['columns'] == 11
    assert overview['missing_cells'] == 4 and overview['duplicate_rows'] == 0
    assert overview['type_counts']['numeric'] == 4

    by_name = {column['name']: column for column in profile['columns']}
    age = by_name['Age']
    assert age['stats']['min'] == 22 and age['stats']['max'] == 51
    assert sum(age['histogram']['counts']) == 40
    assert len(age['histogram']['edges']) == len(age['histogram']['counts']) + 1
    assert by_name['Score']['missing'] == 4 and by_name['Score']['missing_pct'] == 10.0
    assert by_name['Department']['top_values'][0]['count'] == 10
    assert by_name['Hired']['stats'] == {'min': '2020-01-01', 'max': '2021-08-08', 'range_days': 585}
    assert sum(by_name['Hired']['histogram']['counts']) == 40
    assert by_name['Name']['stats']['max_length'] == len('Person 39')


def test_profile_alerts(loaded):
    profile = loaded.get('/profile').get_json()
    kinds = {(alert['kind'], alert['column']) for alert in profile['alerts']}
    assert ('mixed_types', 'Price') in kinds        # "26,6," in an otherwise numeric column
    assert ('missing', 'Score') in kinds            # 10% missing
    assert ('high_correlation', 'Age') in kinds     # Salary is built from Age
    assert profile['correlations'][0]['a'] == 'Age' and profile['correlations'][0]['b'] == 'Salary'
    assert profile['correlations'][0]['r'] > 0.99
    severities = [alert['severity'] for alert in profile['alerts']]
    assert severities == sorted(severities, key=lambda s: s != 'warning')


def test_profile_follows_filters(loaded):
    loaded.post('/apply-filters', json={'filters': {'Department': {'type': 'categorical', 'values': ['IT']}}})
    profile = loaded.get('/profile').get_json()
    assert profile['overview']['rows'] == 10 and profile['overview']['has_filters'] is True
    assert ('constant', 'Department') in {(a['kind'], a['column']) for a in profile['alerts']}


def test_profile_handles_degenerate_data(client):
    frame = pd.DataFrame({'empty': [None, None, None], 'same': [7, 7, 7], 'dup': ['x', 'x', 'x']})
    upload(client, to_xlsx({'S': frame}))
    profile = client.get('/profile').get_json()
    kinds = {(alert['kind'], alert['column']) for alert in profile['alerts']}
    assert ('empty', 'empty') in kinds and ('constant', 'same') in kinds and ('duplicates', None) in kinds
    assert profile['overview']['duplicate_rows'] == 2
    same = next(column for column in profile['columns'] if column['name'] == 'same')
    assert same['histogram']['counts'] == [3]

    # No rows at all after filtering must not crash the profile.
    client.post('/apply-filters', json={'filters': {'same': {'type': 'numeric', 'min': 100}}})
    empty = client.get('/profile')
    assert empty.status_code == 200 and empty.get_json()['overview']['rows'] == 0


# -- plots -------------------------------------------------------------------

@pytest.mark.parametrize('config,traces', [
    ({'type': 'violin', 'columns': ['Age']}, 1),
    ({'type': 'violin', 'columns': ['Age'], 'color': 'Department'}, 4),
    ({'type': 'histogram', 'columns': ['Salary'], 'bins': 8}, 1),
    ({'type': 'histogram', 'columns': ['Salary'], 'color': 'Active'}, 2),
    ({'type': 'box', 'columns': ['Age']}, 1),
    ({'type': 'box', 'columns': ['Age', 'Department']}, 4),
    ({'type': 'box', 'columns': ['Department', 'Age']}, 4),   # order used to matter
    ({'type': 'bar', 'columns': ['Department']}, 1),
    ({'type': 'bar', 'columns': ['Active']}, 1),
    ({'type': 'bar', 'columns': ['Department', 'Active'], 'stacked': True}, 2),
    ({'type': 'bar', 'columns': ['Department', 'Salary'], 'agg': 'mean'}, 1),
    ({'type': 'bar', 'columns': ['Salary', 'Department'], 'agg': 'sum'}, 1),
    ({'type': 'scatter', 'columns': ['Age', 'Salary']}, 1),
    ({'type': 'scatter', 'columns': ['Age', 'Salary'], 'color': 'Department', 'trendline': True}, 5),
    ({'type': 'line', 'columns': ['Hired', 'Salary']}, 1),
    ({'type': 'line', 'columns': ['Hired', 'Salary', 'Age'], 'resample': 'month', 'agg': 'sum'}, 2),
    ({'type': 'line', 'columns': ['Age', 'Salary']}, 1),
    ({'type': 'heatmap', 'columns': []}, 1),
    ({'type': 'heatmap', 'columns': ['Age', 'Salary', 'Score'], 'method': 'spearman'}, 1),
    ({'type': 'pie', 'columns': ['Department']}, 1),
])
def test_every_plot_variant_renders(loaded, config, traces):
    fig = figure(loaded, **config)
    assert len(fig['data']) == traces
    assert fig['layout']['title']['text']


def test_bar_aggregation_values(loaded, processor):
    fig = figure(loaded, type='bar', columns=['Department', 'Salary'], agg='sum')
    expected = processor.data.groupby('Department')['Salary'].sum().sort_values(ascending=False)
    assert fig['data'][0]['x'] == expected.index.tolist()
    assert fig['data'][0]['y'] == expected.tolist()
    assert fig['layout']['title']['text'] == 'Sum of Salary by Department'

    top = figure(loaded, type='bar', columns=['Department'], top_n=2)
    assert len(top['data'][0]['x']) == 2


def test_line_resample_and_duplicate_x(loaded, processor):
    fig = figure(loaded, type='line', columns=['Hired', 'Salary'], resample='year', agg='count')
    assert fig['data'][0]['y'] == [25, 15]
    # Several rows per x value are aggregated instead of drawing a zig-zag.
    by_age = figure(loaded, type='line', columns=['Age', 'Salary'])
    assert len(by_age['data'][0]['x']) == processor.data['Age'].nunique()


def test_heatmap_matrix(loaded):
    fig = figure(loaded, type='heatmap', columns=['Age', 'Salary'])
    z = fig['data'][0]['z']
    assert z[0][0] == 1 and z[1][1] == 1 and z[0][1] == z[1][0] > 0.99


def test_pie_groups_small_slices(client):
    frame = pd.DataFrame({'letter': [chr(65 + i % 15) for i in range(300)], 'n': range(300)})
    upload(client, to_xlsx({'S': frame}))
    fig = figure(client, type='pie', columns=['letter'], top_n=4)
    assert fig['data'][0]['labels'][-1] == 'Other' and len(fig['data'][0]['labels']) == 5
    assert sum(fig['data'][0]['values']) == 300


def test_plots_respect_filters(loaded):
    loaded.post('/apply-filters', json={'filters': {'Department': {'type': 'categorical', 'values': ['IT', 'HR']}}})
    fig = figure(loaded, type='bar', columns=['Department'])
    assert sorted(fig['data'][0]['x']) == ['HR', 'IT'] and sum(fig['data'][0]['y']) == 20


@pytest.mark.parametrize('config,fragment', [
    ({'type': 'nope', 'columns': ['Age']}, 'Unknown plot type'),
    ({'type': 'histogram', 'columns': ['Department']}, 'must be a numeric column'),
    ({'type': 'histogram', 'columns': ['Ghost']}, 'does not exist'),
    ({'type': 'histogram', 'columns': []}, 'needs 1 column'),
    ({'type': 'scatter', 'columns': ['Age']}, 'needs 2 column'),
    ({'type': 'scatter', 'columns': ['Age', 'Salary'], 'color': 'Name'}, 'must be categorical'),
    ({'type': 'bar', 'columns': ['Name']}, 'is a text column'),
    ({'type': 'bar', 'columns': ['Age', 'Salary']}, 'Bar Chart needs'),
    ({'type': 'bar', 'columns': ['Department', 'Salary'], 'agg': 'mode'}, 'Aggregation must be'),
    ({'type': 'line', 'columns': ['Department', 'Salary']}, 'must be a date or numeric'),
    ({'type': 'line', 'columns': ['Age', 'Salary'], 'resample': 'month'}, 'needs a date column'),
    ({'type': 'heatmap', 'columns': ['Age']}, 'at least two numeric'),
    ({'type': 'pie', 'columns': ['Age']}, 'categorical or boolean'),
    ({'type': 'pie', 'columns': ['Department'], 'top_n': 'many'}, 'whole number'),
])
def test_plot_errors_explain_the_problem(loaded, config, fragment):
    response = plot(loaded, **config)
    assert response.status_code == 400
    assert fragment in response.get_json()['error']


def test_plot_with_no_rows_or_too_many_groups(loaded):
    loaded.post('/update-column-type', json={'column': 'Name', 'type': 'categorical'})
    too_many = plot(loaded, type='box', columns=['Age', 'Name'])
    assert too_many.status_code == 400 and '40 distinct values' in too_many.get_json()['error']

    loaded.post('/apply-filters', json={'filters': {'Age': {'type': 'numeric', 'min': 999}}})
    empty = plot(loaded, type='histogram', columns=['Age'])
    assert empty.status_code == 400 and 'No rows' in empty.get_json()['error']


def test_infinite_and_stray_values_do_not_break_plots_or_profile(client):
    import numpy as np

    frame = pd.DataFrame({
        'x': [1.0, np.inf, -np.inf, 2.0, 3.0, 4.0] * 4,
        'y': [float(i) for i in range(24)],
        'when': [pd.Timestamp('2024-01-01') + pd.Timedelta(days=i) if i % 6 else 'unknown' for i in range(24)],
    })
    body = upload(client, to_xlsx({'S': frame})).get_json()
    # A date column with a few stray words stays text; nothing is dropped silently.
    assert body['column_info']['when']['type'] != 'datetime'
    assert body['column_info']['when']['null_count'] == 0

    fig = figure(client, type='scatter', columns=['x', 'y'], trendline=True)
    assert len(fig['data'][0]['x']) == 16          # the 8 infinite points are left out
    assert 'Linear fit' in fig['data'][1]['name']
    for config in ({'type': 'histogram', 'columns': ['x']}, {'type': 'heatmap', 'columns': ['x', 'y']},
                   {'type': 'line', 'columns': ['y', 'x']}):
        figure(client, **config)
    profile = client.get('/profile').get_json()
    stats = next(column for column in profile['columns'] if column['name'] == 'x')['stats']
    assert stats['max'] == 4 and stats['min'] == 1


def test_plot_requires_json_object(loaded):
    assert loaded.post('/plot', data='[]', content_type='application/json').status_code == 400
    assert loaded.post('/plot', data='not json', content_type='text/plain').status_code == 400


# -- AI plot endpoint --------------------------------------------------------

def test_llm_plot_with_test_model(loaded, processor):
    response = loaded.post('/generate-llm-plot', json={'prompt': 'scatter please', 'model': 'test'})
    assert response.status_code == 200
    body = response.get_json()
    assert 'px.scatter' in body['generated_code']
    assert json.loads(body['plot'])['data']


def test_llm_plot_errors(loaded, monkeypatch):
    assert loaded.post('/generate-llm-plot', json={'model': 'test'}).status_code == 400
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    missing_key = loaded.post('/generate-llm-plot', json={'prompt': 'anything'})
    assert missing_key.status_code == 500 and 'GEMINI_API_KEY' in missing_key.get_json()['error']


def test_generated_code_runs_with_restricted_imports():
    import app as app_module

    scope = {'df': pd.DataFrame({'a': [1, 2, 3]}), 'fig': None}
    app_module.safe_exec(
        'import plotly.express as px\n'
        'def build(frame):\n'
        '    return px.bar(frame, y="a")\n'
        'fig = build(df)\n'
        'sizes = [len(df) for _ in range(2)]\n', scope)
    assert scope['fig'] is not None and scope['sizes'] == [3, 3]

    for code in ('import os', 'import subprocess', 'from pathlib import Path',
                 'open("/etc/passwd")', 'eval("1+1")', '__import__("os")'):
        with pytest.raises((ImportError, NameError)):
            app_module.safe_exec(code, {'df': scope['df']})


def test_generated_code_cannot_change_the_dataset(loaded, processor, monkeypatch):
    import app as app_module

    class Vandal:
        def generate_plot_code(self, prompt, df, selected_columns=None):
            return 'df.drop(df.index, inplace=True)\ndf["Age"] = 0\nimport plotly.graph_objects as go\nfig = go.Figure()'

    monkeypatch.setattr(app_module, 'TestLlm', Vandal)
    response = loaded.post('/generate-llm-plot', json={'prompt': 'x', 'model': 'test'})
    assert response.status_code == 200
    assert len(processor.data) == 40 and processor.data['Age'].max() == 51


def test_gemini_prompt_describes_columns(frame):
    """Regression: df.info() returns None, so the prompt said 'Column details: None'."""
    from llm.gemini import GeminiLlm

    description = GeminiLlm._get_data_description(None, frame, ['Age', 'Department'])
    assert 'None' not in description.split('Column details:')[1].split('\n')[0]
    assert "'Age': dtype=int64" in description and "'IT'" in description
    assert "'Salary'" not in description
    assert "'Salary'" in GeminiLlm._get_data_description(None, frame)
