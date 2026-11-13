import json

import pandas as pd

from conftest import make_frame, to_xlsx, upload


def types(response):
    return {name: info['type'] for name, info in response.get_json()['column_info'].items()}


def test_health_before_and_after_upload(client, frame):
    assert client.get('/health').get_json() == {'status': 'ok', 'data_loaded': False}
    assert client.get('/session').get_json() == {'loaded': False}
    assert client.get('/data-preview').status_code == 400
    upload(client, to_xlsx({'Main': frame}))
    assert client.get('/health').get_json()['data_loaded'] is True


def test_upload_detects_types(client, frame):
    response = upload(client, to_xlsx({'Main': frame}))
    body = response.get_json()
    assert response.status_code == 200 and body['success']
    assert body['shape'] == [40, 11]
    assert body['file_name'] == 'data.xlsx' and body['sheet_names'] == ['Main']
    assert len(body['preview']) == 10
    # Columns are reported in file order, not alphabetically.
    assert list(body['column_info']) == body['columns'] == list(frame.columns)
    detected = types(response)
    assert detected['Age'] == 'numeric'
    assert detected['Department'] == 'categorical'
    assert detected['Active'] == 'boolean'
    assert detected['Hired'] == 'datetime'
    assert detected['Name'] == 'text'
    # One malformed value keeps the column non-numeric instead of silently dropping it.
    assert detected['Price'] != 'numeric'
    info = body['column_info']
    assert info['Skills']['has_lists'] and info['Tags']['has_lists']
    assert info['Score']['null_count'] == 4


def test_upload_rejects_bad_input(client):
    assert client.post('/upload', data={}).status_code == 400
    assert upload(client, b'whatever', 'notes.pdf').status_code == 400
    assert upload(client, b'', 'empty.xlsx').status_code == 400
    broken = upload(client, b'this is not a workbook', 'broken.xlsx')
    assert broken.status_code == 400 and 'Excel' in broken.get_json()['error']
    # A failed upload must not leave a half-loaded dataset behind.
    assert client.get('/health').get_json()['data_loaded'] is False


def test_uppercase_extension_is_accepted(client, frame):
    assert upload(client, to_xlsx({'Main': frame}), 'DATA.XLSX').status_code == 200


def test_csv_with_semicolons_and_text_dates(client):
    csv = 'id;city;when;amount\n' + '\n'.join(
        f'{i};{"Ankara" if i % 2 else "İzmir"};2024-01-{i + 1:02d};{i * 1.5}' for i in range(20))
    response = upload(client, csv.encode('utf-8'), 'cities.csv')
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body['columns'] == ['id', 'city', 'when', 'amount'] and body['sheet_names'] == []
    detected = types(response)
    assert detected['when'] == 'datetime' and detected['amount'] == 'numeric'
    assert detected['city'] == 'categorical'
    assert body['preview'][0]['when'] == '2024-01-01'
    assert body['preview'][0]['city'] == 'İzmir'


def test_csv_in_legacy_encoding(client):
    csv = 'name,value\nJosé,1\nZoë,2\n'.encode('cp1252')
    response = upload(client, csv, 'legacy.csv')
    assert response.status_code == 200
    assert response.get_json()['preview'][0]['name'] == 'José'


def test_day_first_dates_are_parsed(client):
    csv = 'when,n\n' + '\n'.join(f'{day:02d}/03/2024,{day}' for day in range(10, 31))
    response = upload(client, csv.encode(), 'dayfirst.csv')
    assert types(response)['when'] == 'datetime'
    assert response.get_json()['preview'][0]['when'] == '2024-03-10'


def test_multi_sheet_selection(client, frame):
    other = pd.DataFrame({'x': [1, 2, 3], 'y': ['a', 'b', 'c']})
    content = to_xlsx({'People': frame, 'Other': other})
    body = upload(client, content).get_json()
    assert body['sheet_names'] == ['People', 'Other'] and body['active_sheet'] == 'People'

    switched = client.post('/select-sheet', json={'sheet': 'Other'})
    assert switched.status_code == 200
    assert switched.get_json()['columns'] == ['x', 'y'] and switched.get_json()['shape'] == [3, 2]
    assert client.get('/session').get_json()['active_sheet'] == 'Other'

    assert client.post('/select-sheet', json={'sheet': 'Missing'}).status_code == 400
    # The failed switch keeps the current sheet loaded.
    assert client.get('/session').get_json()['active_sheet'] == 'Other'
    assert upload(client, content, sheet='Other').get_json()['active_sheet'] == 'Other'


def test_duplicate_and_blank_headers_are_made_unique(client):
    frame = pd.DataFrame([[1, 2, 3, 4]], columns=['a', 'a', None, 2024])
    body = upload(client, to_xlsx({'S': frame})).get_json()
    assert len(set(body['columns'])) == 4
    assert all(isinstance(name, str) and name for name in body['columns'])
    assert '2024' in body['columns']


def test_session_restores_state(loaded):
    loaded.post('/apply-filters', json={'filters': {'Department': {'type': 'categorical', 'values': ['IT']}}})
    session = loaded.get('/session').get_json()
    assert session['loaded'] and session['has_filters']
    assert session['filtered_rows'] == 10 and session['total_rows'] == 40
    assert session['shape'] == [40, 11]


def test_responses_are_strict_json(loaded):
    """NaN/Infinity are not valid JSON and break JSON.parse in the browser."""
    for url in ('/data-preview?per_page=500', '/profile', '/session', '/filter-options?column=Score'):
        text = loaded.get(url).get_data(as_text=True)
        json.loads(text, parse_constant=lambda name: (_ for _ in ()).throw(ValueError(name)))


# -- type overrides ----------------------------------------------------------

def test_type_override_converts_values(loaded, processor):
    response = loaded.post('/update-column-type', json={'column': 'Price', 'type': 'numeric'})
    body = response.get_json()
    assert response.status_code == 200 and body['failed_values'] == 1
    assert body['column_info']['Price']['type'] == 'numeric'
    assert body['column_info']['Price']['null_count'] == 1
    assert pd.api.types.is_numeric_dtype(processor.data['Price'])
    # The numeric plot now works, which it did not when only the label changed.
    assert loaded.post('/plot', json={'type': 'histogram', 'columns': ['Price']}).status_code == 200

    # Going back to text restores the original values, including the bad one.
    loaded.post('/update-column-type', json={'column': 'Price', 'type': 'text'})
    assert '26,6,' in processor.data['Price'].tolist()


def test_type_override_rejects_impossible_conversion(loaded):
    response = loaded.post('/update-column-type', json={'column': 'Name', 'type': 'numeric'})
    assert response.status_code == 400 and 'Name' in response.get_json()['error']
    assert loaded.get('/column-info').get_json()['column_info']['Name']['type'] == 'text'
    assert loaded.post('/update-column-type', json={'column': 'Nope', 'type': 'text'}).status_code == 400
    assert loaded.post('/update-column-type', json={'column': 'Name', 'type': 'banana'}).status_code == 400
    assert loaded.post('/update-column-type', json={'column': 'Name'}).status_code == 400


def test_numeric_as_categorical_can_be_filtered_and_plotted(loaded):
    loaded.post('/update-column-type', json={'column': 'Level', 'type': 'categorical'})
    options = loaded.get('/filter-options?column=Level').get_json()
    assert options['values'] == ['1', '2', '3']
    applied = loaded.post('/apply-filters', json={'filters': {'Level': {'type': 'categorical', 'values': ['2']}}})
    assert applied.get_json()['filtered_rows'] == 13
    assert loaded.post('/plot', json={'type': 'bar', 'columns': ['Level']}).status_code == 200


def test_type_change_drops_stale_filter_on_that_column(loaded):
    loaded.post('/apply-filters', json={'filters': {'Age': {'type': 'numeric', 'min': 40}}})
    body = loaded.post('/update-column-type', json={'column': 'Age', 'type': 'categorical'}).get_json()
    assert body['filter_removed'] is True and body['has_filters'] is False
    assert body['filtered_rows'] == 40


def test_boolean_and_datetime_conversion(client):
    frame = pd.DataFrame({
        'flag': ['yes', 'no', 'Yes', 'maybe'] * 5,
        'serial': [45000 + i for i in range(20)],
        'k': [f'row {i}' for i in range(20)],
    })
    upload(client, to_xlsx({'S': frame}))
    flag = client.post('/update-column-type', json={'column': 'flag', 'type': 'boolean'}).get_json()
    assert flag['failed_values'] == 5
    assert client.get('/filter-options?column=flag').get_json()['values'] == [False, True]
    filtered = client.post('/apply-filters', json={'filters': {'flag': {'type': 'boolean', 'value': True}}})
    assert filtered.get_json()['filtered_rows'] == 10
    client.post('/clear-filters')

    # Numbers in a date column are read as Excel serial days.
    serial = client.post('/update-column-type', json={'column': 'serial', 'type': 'datetime'}).get_json()
    assert serial['failed_values'] == 0
    assert client.get('/filter-options?column=serial').get_json()['min'] == '2023-03-15'


def test_overrides_survive_reupload_without_ghost_columns(client, frame):
    content = to_xlsx({'Main': frame})
    upload(client, content)
    client.post('/expand-column', json={'column': 'Skills'})
    client.post('/update-column-type', json={'column': 'Level', 'type': 'categorical'})

    body = upload(client, content).get_json()
    assert body['column_info']['Level']['type'] == 'categorical'
    assert body['column_info']['Level']['user_set'] is True
    # Expanded columns belong to the previous session and must not reappear.
    assert set(body['column_info']) == set(body['columns']) == set(frame.columns)

    # A different file is unaffected.
    other = upload(client, to_xlsx({'Main': make_frame(30)})).get_json()
    assert other['column_info']['Level']['type'] == 'numeric'


# -- list / set expansion -----------------------------------------------------

def test_expand_positional_splits_unquoted_lists(loaded, processor):
    body = loaded.post('/expand-column', json={'column': 'Skills'}).get_json()
    assert body['new_columns'] == ['Skills_item_1', 'Skills_item_2']
    assert set(processor.data['Skills_item_1']) == {'Python', 'Excel'}
    assert processor.data['Skills_item_2'].isna().sum() == 20
    assert 'Skills_item_1' in body['columns'] and body['shape'] == [40, 13]


def test_expand_onehot_creates_boolean_columns(loaded, processor):
    body = loaded.post('/expand-column', json={'column': 'Tags', 'mode': 'onehot'}).get_json()
    assert sorted(body['new_columns']) == ['Tags [a]', 'Tags [b]']
    assert body['column_info']['Tags [b]']['type'] == 'boolean'
    assert int(processor.data['Tags [a]'].sum()) == 40 and int(processor.data['Tags [b]'].sum()) == 20
    filtered = loaded.post('/apply-filters', json={'filters': {'Tags [b]': {'type': 'boolean', 'value': True}}})
    assert filtered.get_json()['filtered_rows'] == 20


def test_expanded_columns_survive_filtering(loaded, processor):
    """Regression: filters used to rebuild the data without expanded columns."""
    loaded.post('/expand-column', json={'column': 'Skills', 'mode': 'onehot'})
    loaded.post('/apply-filters', json={'filters': {'Department': {'type': 'categorical', 'values': ['IT']}}})
    assert 'Skills [Python]' in processor.data.columns and len(processor.data) == 10
    assert loaded.post('/plot', json={'type': 'bar', 'columns': ['Skills [Python]']}).status_code == 200
    loaded.post('/clear-filters')
    assert 'Skills [Python]' in processor.data.columns and len(processor.data) == 40


def test_expand_errors(loaded):
    assert loaded.post('/expand-column', json={}).status_code == 400
    assert loaded.post('/expand-column', json={'column': 'Nope'}).status_code == 400
    assert loaded.post('/expand-column', json={'column': 'Skills', 'mode': 'weird'}).status_code == 400
