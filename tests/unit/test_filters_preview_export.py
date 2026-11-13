from io import BytesIO

import pandas as pd
import pytest


def apply(client, filters):
    return client.post('/apply-filters', json={'filters': filters})


def rows(client, filters):
    response = apply(client, filters)
    assert response.status_code == 200, response.get_json()
    return response.get_json()['filtered_rows']


def test_categorical_numeric_boolean_filters(loaded):
    assert rows(loaded, {'Department': {'type': 'categorical', 'values': ['IT', 'HR']}}) == 20
    assert rows(loaded, {'Age': {'type': 'numeric', 'min': 30, 'max': 40}}) == \
        sum(1 for i in range(40) if 30 <= 22 + (i * 7) % 30 <= 40)
    assert rows(loaded, {'Active': {'type': 'boolean', 'value': False}}) == 14
    # Filters combine with AND.
    assert rows(loaded, {'Department': {'type': 'categorical', 'values': ['IT']},
                         'Active': {'type': 'boolean', 'value': True}}) == 6


def test_empty_filter_configs_are_no_ops(loaded):
    assert rows(loaded, {'Department': {'type': 'categorical', 'values': []},
                         'Name': {'type': 'text', 'value': ''},
                         'Age': {'type': 'numeric'},
                         'Ghost column': {'type': 'numeric', 'min': 1}}) == 40


def test_text_contains_is_literal(loaded):
    """Regression: 'contains' was treated as a regex, so '(' crashed the filter."""
    assert rows(loaded, {'Name': {'type': 'text', 'search_type': 'contains', 'value': 'Person 1'}}) == 11
    assert rows(loaded, {'Name': {'type': 'text', 'search_type': 'contains', 'value': 'C++ ('}}) == 0
    assert rows(loaded, {'Price': {'type': 'text', 'search_type': 'contains', 'value': '.'}}) == 0
    assert rows(loaded, {'Name': {'type': 'text', 'value': 'person 1', 'case_sensitive': True}}) == 0
    assert rows(loaded, {'Name': {'type': 'text', 'value': 'Person 1', 'negate': True}}) == 29


def test_text_regex_and_invalid_regex(loaded):
    assert rows(loaded, {'Name': {'type': 'text', 'search_type': 'regex', 'value': r'^Person [0-9]$'}}) == 10
    bad = apply(loaded, {'Name': {'type': 'text', 'search_type': 'regex', 'value': '('}})
    assert bad.status_code == 400 and 'regular expression' in bad.get_json()['error']
    # The rejected filter must not replace the previous state.
    assert loaded.get('/filter-status').get_json()['filtered_rows'] == 10


def test_datetime_filter_is_inclusive(loaded):
    assert rows(loaded, {'Hired': {'type': 'datetime', 'start': '2020-01-16'}}) == 39
    assert rows(loaded, {'Hired': {'type': 'datetime', 'end': '2020-01-16'}}) == 2
    assert rows(loaded, {'Hired': {'type': 'datetime', 'start': '2020-01-16', 'end': '2020-01-31'}}) == 2
    assert apply(loaded, {'Hired': {'type': 'datetime', 'start': 'not a date'}}).status_code == 400


def test_nulls_are_excluded_unless_requested(loaded):
    assert rows(loaded, {'Score': {'type': 'numeric', 'min': 0}}) == 36
    assert rows(loaded, {'Score': {'type': 'numeric', 'min': 20, 'include_nulls': True}}) == 22


def test_invalid_filter_payloads(loaded):
    assert apply(loaded, {'Age': {'type': 'numeric', 'min': 'abc'}}).status_code == 400
    assert apply(loaded, {'Age': {'type': 'mystery'}}).status_code == 400
    assert loaded.post('/apply-filters', json={'filters': ['nope']}).status_code == 400


def test_clear_filters_and_status(loaded):
    rows(loaded, {'Department': {'type': 'categorical', 'values': ['IT']}})
    status = loaded.get('/filter-status').get_json()
    assert status == {'has_filters': True, 'filtered_rows': 10, 'total_rows': 40,
                      'active_filters': {'Department': {'type': 'categorical', 'values': ['IT']}}}
    cleared = loaded.post('/clear-filters').get_json()
    assert cleared['success'] and cleared['total_rows'] == 40 and not cleared['has_filters']


@pytest.mark.parametrize('column,expected_type', [
    ('Department', 'categorical'), ('Age', 'numeric'), ('Name', 'text'),
    ('Active', 'boolean'), ('Hired', 'datetime'),
])
def test_filter_options_for_every_type(loaded, column, expected_type):
    by_query = loaded.get(f'/filter-options?column={column}').get_json()
    by_path = loaded.get(f'/filter-options/{column}').get_json()
    assert by_query == by_path and by_query['type'] == expected_type


def test_filter_options_details(loaded):
    assert loaded.get('/filter-options?column=Department').get_json()['values'] == ['Finance', 'HR', 'IT', 'Ops']
    age = loaded.get('/filter-options?column=Age').get_json()
    assert age['min'] == 22 and age['max'] == 51
    hired = loaded.get('/filter-options?column=Hired').get_json()
    assert hired == {'type': 'datetime', 'min': '2020-01-01', 'max': '2021-08-08'}
    assert loaded.get('/filter-options?column=Nope').status_code == 404
    assert loaded.get('/filter-options').status_code == 400


def test_filter_options_for_awkward_column_names(client):
    from conftest import to_xlsx, upload
    frame = pd.DataFrame({'a/b?c#d': [1, 2, 3], 'x': ['p', 'q', 'r']})
    upload(client, to_xlsx({'S': frame}))
    response = client.get('/filter-options', query_string={'column': 'a/b?c#d'})
    assert response.status_code == 200 and response.get_json()['max'] == 3


# -- preview -----------------------------------------------------------------

def test_preview_pagination(loaded):
    page = loaded.get('/data-preview?page=2&per_page=15').get_json()
    assert page['page'] == 2 and page['total_pages'] == 3 and page['total_rows'] == 40
    assert len(page['data']) == 15 and page['data'][0]['Name'] == 'Person 15'
    assert page['data'][0]['Hired'] == '2020-08-13'
    # Out-of-range pages clamp instead of returning nothing.
    assert loaded.get('/data-preview?page=99&per_page=15').get_json()['page'] == 3
    assert loaded.get('/data-preview?page=-4&per_page=0').get_json()['page'] == 1


def test_preview_sort_and_search(loaded):
    desc = loaded.get('/data-preview?sort_by=Salary&sort_dir=desc&per_page=5').get_json()['data']
    salaries = [row['Salary'] for row in desc]
    assert salaries == sorted(salaries, reverse=True)

    # Missing values sort last in both directions.
    asc = loaded.get('/data-preview?sort_by=Score&per_page=500').get_json()['data']
    assert [row['Score'] for row in asc][-4:] == [None] * 4

    found = loaded.get('/data-preview?search=person 3').get_json()
    assert found['total_rows'] == 11 and found['filtered_rows'] == 40
    assert loaded.get('/data-preview?search=2020-01-16').get_json()['total_rows'] == 1
    assert loaded.get('/data-preview?search=zzz').get_json()['data'] == []


def test_preview_respects_filters(loaded):
    rows(loaded, {'Department': {'type': 'categorical', 'values': ['Ops']}})
    page = loaded.get('/data-preview?per_page=500').get_json()
    assert page['total_rows'] == 10 and page['unfiltered_rows'] == 40
    assert {row['Department'] for row in page['data']} == {'Ops'}


# -- export ------------------------------------------------------------------

def test_export_csv_respects_filters(loaded):
    rows(loaded, {'Department': {'type': 'categorical', 'values': ['IT']}})
    response = loaded.get('/export?format=csv')
    assert response.status_code == 200
    assert 'data_filtered.csv' in response.headers['Content-Disposition']
    exported = pd.read_csv(BytesIO(response.data))
    assert len(exported) == 10 and set(exported['Department']) == {'IT'}
    assert response.data.startswith(b'\xef\xbb\xbf')  # BOM so Excel reads UTF-8

    everything = loaded.get('/export?format=csv&scope=all')
    assert 'data.csv' in everything.headers['Content-Disposition']
    assert len(pd.read_csv(BytesIO(everything.data))) == 40


def test_export_xlsx_round_trips(loaded):
    loaded.post('/expand-column', json={'column': 'Skills', 'mode': 'onehot'})
    response = loaded.get('/export?format=xlsx')
    exported = pd.read_excel(BytesIO(response.data))
    # 11 original columns + one indicator each for Python, SQL and Excel
    assert exported.shape == (40, 14) and 'Skills [Python]' in exported.columns
    assert loaded.get('/export?format=pdf').status_code == 400
