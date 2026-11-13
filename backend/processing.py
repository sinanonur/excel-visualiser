"""Dataset state for the Excel visualiser: loading, typing, filtering, profiling.

Three frames are kept so that every operation has one obvious source:

* ``raw_data``      - values exactly as loaded (plus expanded list columns).
                      Type overrides always convert from here, so switching a
                      column to numeric and back to text loses nothing.
* ``original_data`` - the typed, *unfiltered* working frame.
* ``data``          - the typed, *filtered* frame used by previews, plots,
                      the profile and exports. It is ``original_data`` itself
                      when no filter is active.
"""

import ast
import datetime as dt
import decimal
import math
import os
import re
import shelve
import tempfile
from io import BytesIO

import numpy as np
import pandas as pd

from plots import PlotError, build_plot, figure_to_json

COLUMN_TYPES = ('numeric', 'categorical', 'text', 'datetime', 'boolean')
EXCEL_EXTENSIONS = ('.xlsx', '.xlsm', '.xls')
DELIMITED_EXTENSIONS = ('.csv', '.tsv', '.txt')
SUPPORTED_EXTENSIONS = EXCEL_EXTENSIONS + DELIMITED_EXTENSIONS

CACHE_FILE = 'column_type_overrides'
CACHE_TTL_DAYS = 2

MAX_CATEGORY_OPTIONS = 2000
MAX_ONEHOT_ITEMS = 50
EXCEL_MAX_ROWS = 1_048_576

# Data-quality alert thresholds (see DataProcessor.profile).
MISSING_INFO_PCT = 5
MISSING_WARNING_PCT = 50
HIGH_CARDINALITY = 50
SKEW_THRESHOLD = 2
HIGH_CORRELATION = 0.9
CORRELATION_LIST_MIN = 0.5
MOSTLY_NUMERIC_SHARE = 0.8
MAX_CORRELATION_COLUMNS = 30

_TRUE_WORDS = {'true', 't', 'yes', 'y', '1', '1.0', 'on'}
_FALSE_WORDS = {'false', 'f', 'no', 'n', '0', '0.0', 'off'}

_DATE_PATTERN = re.compile(
    r'^\s*(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})'
    r'([T\s]\d{1,2}:\d{2}(:\d{2})?(\.\d+)?\s*(Z|[+-]\d{2}:?\d{2})?)?\s*$'
)
_LIST_PATTERN = re.compile(r'^\s*(\[.*\]|\{.*\})\s*$', re.DOTALL)


class DataError(ValueError):
    """A problem the user can act on; the message is shown in the UI."""


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def to_jsonable(obj):
    """Recursively convert pandas/numpy values into strict-JSON-safe values.

    NaN/NaT/inf become ``None`` because ``NaN`` and ``Infinity`` are not valid
    JSON and make ``JSON.parse`` in the browser fail.
    """
    if obj is None or isinstance(obj, (str, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(key): to_jsonable(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [to_jsonable(item) for item in obj]
    if isinstance(obj, np.ndarray):
        return [to_jsonable(item) for item in obj.tolist()]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        value = float(obj)
        return value if math.isfinite(value) else None
    if isinstance(obj, decimal.Decimal):
        value = float(obj)
        return value if math.isfinite(value) else None
    if obj is pd.NaT or obj is pd.NA:
        return None
    if isinstance(obj, pd.Timestamp):
        return _format_timestamp(obj)
    if isinstance(obj, (dt.datetime, dt.date, dt.time)):
        return obj.isoformat()
    if isinstance(obj, (pd.Timedelta, dt.timedelta, bytes)):
        return str(obj)
    if isinstance(obj, np.datetime64):
        return _format_timestamp(pd.Timestamp(obj))
    if isinstance(obj, np.generic):
        return to_jsonable(obj.item())
    return obj


# Kept under the old name for callers that imported it from app.py.
convert_to_json_serializable = to_jsonable


def _format_timestamp(value):
    if value is pd.NaT or pd.isna(value):
        return None
    if value == value.normalize():
        return value.strftime('%Y-%m-%d')
    return value.strftime('%Y-%m-%d %H:%M:%S')


def _format_datetime_series(series):
    """Datetime series -> object series of readable strings (None for NaT)."""
    valid = series.dropna()
    date_only = valid.empty or bool((valid == valid.dt.normalize()).all())
    text = series.dt.strftime('%Y-%m-%d' if date_only else '%Y-%m-%d %H:%M:%S')
    return text.astype(object).where(series.notna(), None)


def frame_to_records(frame):
    """Rows of ``frame`` as JSON-safe dicts."""
    out = frame.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = _format_datetime_series(out[col])
    return to_jsonable(out.to_dict('records'))


def _round(value, digits=4):
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return round(value, digits) if math.isfinite(value) else None


# ---------------------------------------------------------------------------
# Type-override cache (keeps a user's manual column types across re-uploads)
# ---------------------------------------------------------------------------

def _cache_path():
    cache_dir = os.environ.get('EXCEL_VISUALIZER_CACHE_DIR') or os.path.join(
        tempfile.gettempdir(), 'excel_visualizer_cache')
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, CACHE_FILE)


def load_type_overrides(key):
    """Return ``{column: type}`` saved for this file, dropping expired entries.

    The cache is a convenience: any failure (locked or corrupt shelf) is
    treated as a miss instead of breaking the upload.
    """
    try:
        with shelve.open(_cache_path()) as cache:
            cutoff = dt.datetime.now() - dt.timedelta(days=CACHE_TTL_DAYS)
            for stale in [k for k, v in cache.items() if v.get('timestamp', cutoff) <= cutoff]:
                del cache[stale]
            entry = cache.get(key)
            return dict(entry['overrides']) if entry else {}
    except Exception as exc:  # pragma: no cover - depends on the dbm backend
        print(f'Type cache unavailable: {exc}')
        return {}


def save_type_overrides(key, overrides):
    try:
        with shelve.open(_cache_path()) as cache:
            if overrides:
                cache[key] = {'overrides': dict(overrides), 'timestamp': dt.datetime.now()}
            elif key in cache:
                del cache[key]
    except Exception as exc:  # pragma: no cover
        print(f'Type cache unavailable: {exc}')


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _normalise_columns(frame):
    """Give every column a unique, non-empty string name."""
    names, seen = [], set()
    for position, original in enumerate(frame.columns):
        name = '' if (isinstance(original, float) and math.isnan(original)) else str(original).strip()
        if not name or name.startswith('Unnamed:'):
            name = f'Column {position + 1}'
        base, suffix = name, 2
        while name in seen:
            name = f'{base}_{suffix}'
            suffix += 1
        seen.add(name)
        names.append(name)
    frame.columns = names
    return frame


def _read_delimited(content, extension):
    """Read CSV/TSV text, sniffing the delimiter and tolerating legacy encodings."""
    separator = '\t' if extension == '.tsv' else None
    last_error = None
    for encoding in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            return pd.read_csv(BytesIO(content), sep=separator, engine='python', encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
        except pd.errors.EmptyDataError:
            raise DataError('The file is empty')
        except Exception as exc:
            raise DataError(f'Could not read the file: {exc}')
    raise DataError(f'Could not decode the file: {last_error}')


def parse_list_cell(value):
    """Split a ``[a, b]`` / ``{a, b}`` cell into items.

    Python literals (``['a', 'b']``) are parsed exactly; the far more common
    spreadsheet form with bare words (``[Python, SQL]``) falls back to a comma
    split. Sets are sorted so the result is deterministic.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    text = str(value).strip()
    if len(text) < 2 or (text[0], text[-1]) not in (('[', ']'), ('{', '}')):
        return [text] if text else []
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError, MemoryError, RecursionError):
        parts = [part.strip().strip('\'"').strip() for part in text[1:-1].split(',')]
        items = [part for part in parts if part]
        return sorted(set(items)) if text[0] == '{' else items
    if isinstance(parsed, (set, frozenset)):
        return sorted(parsed, key=str)
    if isinstance(parsed, dict):
        return list(parsed.keys())
    if isinstance(parsed, (list, tuple)):
        return list(parsed)
    return [parsed]


def _to_boolean(series):
    def convert(value):
        if value is None or (not isinstance(value, str) and pd.isna(value)):
            return None
        if isinstance(value, (bool, np.bool_)):
            return bool(value)
        word = str(value).strip().lower()
        if word in _TRUE_WORDS:
            return True
        if word in _FALSE_WORDS:
            return False
        return None

    converted = series.map(convert).astype(object)
    return converted.astype(bool) if converted.notna().all() and len(converted) else converted


def _to_datetime(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        converted = series
    elif pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
        # Numbers in a date column are almost always Excel serial days.
        numeric = pd.to_numeric(series, errors='coerce')
        plausible = numeric.where((numeric >= 1) & (numeric <= 2_958_465))
        converted = pd.to_datetime(plausible, unit='D', origin='1899-12-30', errors='coerce')
    else:
        converted = _parse_date_strings(series)
    if getattr(converted.dt, 'tz', None) is not None:
        converted = converted.dt.tz_localize(None)
    return converted


def _parse_date_strings(series):
    """Parse text dates, trying month-first then day-first and keeping the better."""
    best = None
    for dayfirst in (False, True):
        try:
            parsed = pd.to_datetime(series, errors='coerce', dayfirst=dayfirst, utc=False)
        except (ValueError, TypeError, OverflowError):
            continue
        if not pd.api.types.is_datetime64_any_dtype(parsed):
            try:
                parsed = pd.to_datetime(series, errors='coerce', dayfirst=dayfirst, utc=True)
            except (ValueError, TypeError, OverflowError):
                continue
        if best is None or parsed.notna().sum() > best.notna().sum():
            best = parsed
        if best.notna().sum() == series.notna().sum():
            break
    if best is None:
        best = pd.Series(pd.NaT, index=series.index, dtype='datetime64[ns]')
    return best


def convert_series(series, new_type):
    """Convert ``series`` to ``new_type``; returns ``(converted, failed_count)``."""
    if new_type == 'numeric':
        source = series.astype(float) if pd.api.types.is_bool_dtype(series) else series
        if pd.api.types.is_datetime64_any_dtype(source):
            raise DataError('Date columns cannot be converted to numbers')
        converted = pd.to_numeric(source, errors='coerce')
    elif new_type == 'datetime':
        converted = _to_datetime(series)
    elif new_type == 'boolean':
        converted = _to_boolean(series)
    else:
        return series.copy(), 0
    failed = int(converted.isna().sum() - series.isna().sum())
    return converted, max(failed, 0)


# ---------------------------------------------------------------------------
# DataProcessor
# ---------------------------------------------------------------------------

class DataProcessor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.raw_data = None
        self.original_data = None
        self.data = None
        self.filtered_data = None
        self.column_info = {}
        self.active_filters = {}
        self.type_overrides = {}
        self.file_hash = None
        self.file_name = None
        self.file_content = None
        self.sheet_names = []
        self.active_sheet = None

    # -- loading ------------------------------------------------------------

    def load_file(self, content, filename, sheet=None):
        """Load a spreadsheet or delimited file. Raises DataError on bad input."""
        extension = os.path.splitext(filename or '')[1].lower()
        sheet_names, active_sheet = [], None

        if extension in DELIMITED_EXTENSIONS:
            frame = _read_delimited(content, extension)
        elif extension in EXCEL_EXTENSIONS:
            try:
                book = pd.ExcelFile(BytesIO(content))
            except ImportError as exc:
                raise DataError(f'This Excel format needs an extra package: {exc}')
            except Exception as exc:
                raise DataError(f'Could not read the Excel file: {exc}')
            sheet_names = [str(name) for name in book.sheet_names]
            if not sheet_names:
                raise DataError('The workbook has no sheets')
            active_sheet = sheet_names[0] if sheet in (None, '') else str(sheet)
            if active_sheet not in sheet_names:
                raise DataError(f'Sheet "{active_sheet}" not found in the workbook')
            try:
                frame = book.parse(book.sheet_names[sheet_names.index(active_sheet)])
            except Exception as exc:
                raise DataError(f'Could not read sheet "{active_sheet}": {exc}')
        else:
            raise DataError('Unsupported file type. Upload .xlsx, .xls, .xlsm, .csv or .tsv')

        if frame.shape[1] == 0:
            where = f'Sheet "{active_sheet}"' if active_sheet else 'The file'
            raise DataError(f'{where} has no columns')

        frame = _normalise_columns(frame).reset_index(drop=True)

        self.reset()
        self.file_content = content
        self.file_name = filename
        self.sheet_names = sheet_names
        self.active_sheet = active_sheet
        self.raw_data = frame
        self.original_data = frame.copy()
        self.detect_column_types()
        self.data = self.original_data
        return True

    def load_excel(self, file_content):
        """Backwards-compatible wrapper: load .xlsx bytes, return success flag."""
        try:
            return self.load_file(file_content, 'upload.xlsx')
        except DataError as exc:
            print(f'Error loading Excel: {exc}')
            return False

    def select_sheet(self, sheet):
        if not self.file_content or not self.sheet_names:
            raise DataError('The loaded file has no sheets to switch between')
        file_hash = self.file_hash
        self.load_file(self.file_content, self.file_name, sheet=sheet)
        self.file_hash = file_hash
        self.restore_overrides()

    @property
    def cache_key(self):
        return f'{self.file_hash}:{self.active_sheet or ""}' if self.file_hash else None

    def restore_overrides(self):
        """Re-apply the manual column types remembered for this file."""
        if not self.cache_key:
            return
        for column, new_type in load_type_overrides(self.cache_key).items():
            if column in self.original_data.columns and new_type in COLUMN_TYPES:
                try:
                    self.set_column_type(column, new_type, persist=False)
                except DataError:
                    continue

    # -- typing -------------------------------------------------------------

    def detect_column_types(self, columns=None):
        """Infer types for ``columns`` (default: all) from the raw values."""
        if columns is None:
            self.column_info = {}
            columns = list(self.raw_data.columns)
        for col in columns:
            override = self.type_overrides.get(col)
            if override:
                converted, _ = convert_series(self.raw_data[col], override)
                col_type = override
            else:
                converted, col_type = self._infer_column(self.raw_data[col])
            self.original_data[col] = converted
            self.column_info[col] = self._describe_column(col, col_type, bool(override))

    def _infer_column(self, series):
        non_null = series.dropna()
        if non_null.empty:
            return series, 'empty'
        if pd.api.types.is_bool_dtype(series):
            return series, 'boolean'
        if pd.api.types.is_datetime64_any_dtype(series):
            return _to_datetime(series), 'datetime'
        if pd.api.types.is_numeric_dtype(series):
            return series, 'numeric'

        inferred = pd.api.types.infer_dtype(non_null, skipna=True)
        if inferred == 'boolean':
            return _to_boolean(series), 'boolean'
        if inferred in ('datetime', 'date', 'datetime64'):
            return _to_datetime(series), 'datetime'

        numeric = pd.to_numeric(non_null, errors='coerce')
        if numeric.notna().all():
            return pd.to_numeric(series, errors='coerce'), 'numeric'

        if inferred == 'string' and self._looks_like_dates(non_null):
            parsed = _to_datetime(series)
            if parsed.notna().sum() >= 0.95 * len(non_null):
                return parsed, 'datetime'

        unique = self._count_unique(non_null)
        ratio = unique / max(len(series), 1)
        is_categorical = unique < 4 or ratio < 0.1 or (unique <= 20 and ratio <= 0.5)
        return series, 'categorical' if is_categorical else 'text'

    @staticmethod
    def _looks_like_dates(non_null):
        sample = non_null.head(200).astype(str)
        matches = sum(1 for value in sample if _DATE_PATTERN.match(value))
        return matches >= 0.95 * len(sample)

    @staticmethod
    def _count_unique(series):
        try:
            return int(series.nunique())
        except TypeError:  # unhashable cell values
            return int(series.astype(str).nunique())

    def _describe_column(self, col, col_type, user_set=False):
        series = self.original_data[col]
        non_null = series.dropna()
        is_texty = series.dtype == object
        return {
            'type': col_type,
            'has_lists': bool(is_texty and len(non_null) and self.detect_lists_or_sets(non_null)),
            'unique_values': self._count_unique(non_null),
            'null_count': int(series.isna().sum()),
            'user_set': user_set,
        }

    def detect_lists_or_sets(self, series):
        sample = series.head(100).astype(str)
        matches = sum(1 for value in sample if _LIST_PATTERN.match(value))
        return matches > len(sample) * 0.3

    def set_column_type(self, column, new_type, persist=True):
        """Change a column's type *and convert its values*.

        Returns ``{'failed_values', 'filter_removed'}``. Values that cannot be
        converted become missing; if none can, the change is rejected.
        """
        if self.original_data is None or column not in self.original_data.columns:
            raise DataError('Column not found')
        if new_type not in COLUMN_TYPES:
            raise DataError(f'Unknown column type "{new_type}"')

        has_raw = self.raw_data is not None and column in self.raw_data.columns
        source = self.raw_data[column] if has_raw else self.original_data[column]
        converted, failed = convert_series(source, new_type)
        non_null = int(source.notna().sum())
        if non_null and failed >= non_null:
            raise DataError(f'None of the values in "{column}" can be read as {new_type}')

        self.original_data[column] = converted
        self.type_overrides[column] = new_type
        self.column_info[column] = self._describe_column(column, new_type, user_set=True)
        # A filter built for the old type no longer means anything.
        filter_removed = self.active_filters.pop(column, None) is not None
        self._refilter()
        if persist and self.cache_key:
            save_type_overrides(self.cache_key, self.type_overrides)
        return {'failed_values': failed, 'filter_removed': filter_removed}

    # -- list / set expansion -----------------------------------------------

    def expand_list_column(self, column_name, mode='positional', max_items=MAX_ONEHOT_ITEMS):
        """Expand ``[a, b]`` / ``{a, b}`` cells into new columns.

        ``positional`` adds ``<col>_item_1..n`` (the n-th item of each cell).
        ``onehot`` adds one boolean ``<col> [<item>]`` column per distinct item
        (the ``max_items`` most frequent), which is what filters and bar
        charts need. Returns the new column names.
        """
        if self.original_data is None or column_name not in self.original_data.columns:
            raise DataError('Column not found')
        if mode not in ('positional', 'onehot'):
            raise DataError(f'Unknown expansion mode "{mode}"')

        source = self.raw_data[column_name] if column_name in self.raw_data.columns \
            else self.original_data[column_name]
        cells = [parse_list_cell(value) for value in source]
        index = self.raw_data.index
        new_columns = {}

        if mode == 'positional':
            width = max((len(items) for items in cells), default=0)
            for position in range(width):
                values = [items[position] if position < len(items) else None for items in cells]
                new_columns[f'{column_name}_item_{position + 1}'] = pd.Series(values, index=index, dtype=object)
        else:
            cell_sets = [{str(item) for item in items} for items in cells]
            counts = pd.Series([item for items in cell_sets for item in items], dtype=object).value_counts()
            for item in counts.head(max_items).index:
                new_columns[f'{column_name} [{item}]'] = pd.Series(
                    [item in items for items in cell_sets], index=index, dtype=bool)

        if not new_columns:
            raise DataError(f'No list items found in "{column_name}"')

        for name, values in new_columns.items():
            self.raw_data[name] = values
            self.original_data[name] = values
            self.type_overrides.pop(name, None)
        self.detect_column_types(list(new_columns))
        self._refilter()
        return list(new_columns)

    # -- filtering ----------------------------------------------------------

    def apply_filters(self, filters):
        """Replace the active filters. Raises DataError on an invalid filter
        and leaves the previous filters in place."""
        if not isinstance(filters, dict):
            raise DataError('Filters must be an object keyed by column name')
        cleaned = {col: cfg for col, cfg in filters.items() if isinstance(cfg, dict)}
        mask = self._combined_mask(cleaned)
        self.active_filters = cleaned
        self._set_filtered(mask)
        return True

    def clear_filters(self):
        self.active_filters = {}
        self._set_filtered(None)

    def _refilter(self):
        try:
            mask = self._combined_mask(self.active_filters)
        except DataError:
            self.active_filters, mask = {}, None
        self._set_filtered(mask)

    def _set_filtered(self, mask):
        if mask is None:
            self.data = self.original_data
            self.filtered_data = None
        else:
            self.data = self.original_data[mask]
            self.filtered_data = self.data

    def _combined_mask(self, filters):
        frame = self.original_data
        mask = None
        for column, config in filters.items():
            if column not in frame.columns:
                continue
            column_mask = self._filter_mask(column, frame[column], config)
            if column_mask is None:
                continue
            mask = column_mask if mask is None else (mask & column_mask)
        return mask

    @staticmethod
    def _filter_mask(column, series, config):
        """Boolean mask for one column filter, or None if the filter is a no-op."""
        filter_type = config.get('type')
        present = series.notna()

        if filter_type == 'categorical':
            values = config.get('values') or []
            if not values:
                return None
            # Options are offered as strings, so compare as strings; otherwise
            # numeric or boolean categories never match.
            mask = series.astype(str).isin([str(v) for v in values]) & present

        elif filter_type == 'numeric':
            try:
                low = None if config.get('min') is None else float(config['min'])
                high = None if config.get('max') is None else float(config['max'])
            except (TypeError, ValueError):
                raise DataError(f'Numeric range for "{column}" must be numbers')
            if low is None and high is None:
                return None
            numbers = pd.to_numeric(series, errors='coerce')
            mask = numbers.notna()
            if low is not None:
                mask &= numbers >= low
            if high is not None:
                mask &= numbers <= high

        elif filter_type == 'text':
            value = config.get('value') or ''
            if not value:
                return None
            is_regex = config.get('search_type', 'contains') == 'regex'
            if is_regex:
                try:
                    re.compile(value)
                except re.error as exc:
                    raise DataError(f'Invalid regular expression for "{column}": {exc}')
            mask = series.astype(str).str.contains(
                value, case=bool(config.get('case_sensitive', False)), regex=is_regex, na=False) & present
            if config.get('negate'):
                mask = ~mask & present

        elif filter_type == 'boolean':
            wanted = config.get('value')
            if wanted is None:
                return None
            wanted = bool(wanted)
            mask = _to_boolean(series).map(lambda v: v is not None and not pd.isna(v) and bool(v) == wanted)
            mask = mask.astype(bool)

        elif filter_type == 'datetime':
            start, end = config.get('start'), config.get('end')
            if not start and not end:
                return None
            dates = pd.to_datetime(series, errors='coerce')
            mask = dates.notna()
            try:
                if start:
                    mask &= dates >= pd.Timestamp(start)
                if end:
                    end_ts = pd.Timestamp(end)
                    if len(str(end)) <= 10:  # a bare date includes that whole day
                        mask &= dates < end_ts + pd.Timedelta(days=1)
                    else:
                        mask &= dates <= end_ts
            except (ValueError, TypeError):
                raise DataError(f'Invalid date range for "{column}"')

        else:
            raise DataError(f'Unknown filter type "{filter_type}" for "{column}"')

        if config.get('include_nulls'):
            mask = mask | ~present
        return mask

    def get_filter_options(self, column):
        """Values/ranges the UI needs to build a filter for ``column``."""
        if self.original_data is None or column not in self.original_data.columns:
            return None
        series = self.original_data[column]
        non_null = series.dropna()
        col_type = self.column_info.get(column, {}).get('type')

        if col_type == 'categorical':
            values = sorted(non_null.astype(str).unique().tolist())
            return {'type': 'categorical', 'values': values[:MAX_CATEGORY_OPTIONS],
                    'total_values': len(values), 'truncated': len(values) > MAX_CATEGORY_OPTIONS}

        if col_type == 'numeric':
            numbers = pd.to_numeric(non_null, errors='coerce').dropna()
            if numbers.empty:
                return {'type': 'numeric', 'min': None, 'max': None, 'mean': None, 'std': None}
            return {'type': 'numeric', 'min': float(numbers.min()), 'max': float(numbers.max()),
                    'mean': float(numbers.mean()), 'std': float(numbers.std()) if len(numbers) > 1 else 0.0}

        if col_type == 'text':
            return {'type': 'text', 'sample_values': non_null.astype(str).drop_duplicates().head(10).tolist()}

        if col_type == 'boolean':
            values = sorted({bool(v) for v in _to_boolean(non_null).dropna()})
            return {'type': 'boolean', 'values': values}

        if col_type == 'datetime':
            dates = pd.to_datetime(non_null, errors='coerce').dropna()
            if dates.empty:
                return {'type': 'datetime', 'min': None, 'max': None}
            return {'type': 'datetime', 'min': dates.min().strftime('%Y-%m-%d'),
                    'max': dates.max().strftime('%Y-%m-%d')}

        return None

    # -- preview / export ---------------------------------------------------

    def get_page(self, page=1, per_page=50, sort_by=None, sort_dir='asc', search=None):
        """One page of the filtered data, optionally searched and sorted."""
        frame = self.data
        per_page = max(1, min(int(per_page or 50), 500))

        if search:
            needle = str(search)
            hits = pd.Series(False, index=frame.index)
            for col in frame.columns:
                column = frame[col]
                text = _format_datetime_series(column).astype(str) \
                    if pd.api.types.is_datetime64_any_dtype(column) else column.astype(str)
                hits |= text.str.contains(needle, case=False, regex=False, na=False) & column.notna()
            frame = frame[hits]

        if sort_by and sort_by in frame.columns:
            ascending = str(sort_dir).lower() != 'desc'
            try:
                frame = frame.sort_values(sort_by, ascending=ascending, na_position='last', kind='stable')
            except TypeError:  # mixed types in one column: sort by text form
                frame = frame.sort_values(sort_by, ascending=ascending, na_position='last', kind='stable',
                                          key=lambda s: s.astype(str))

        total = len(frame)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(int(page or 1), total_pages))
        start = (page - 1) * per_page
        return {
            'data': frame_to_records(frame.iloc[start:start + per_page]),
            'columns': list(self.data.columns),
            'total_rows': total,
            'filtered_rows': len(self.data),
            'unfiltered_rows': len(self.original_data),
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
        }

    def export(self, file_format='csv', scope='filtered'):
        """Serialise the data. Returns ``(bytes, filename, mimetype)``."""
        frame = self.original_data if scope == 'all' else self.data
        stem = os.path.splitext(os.path.basename(self.file_name or 'data'))[0] or 'data'
        if scope != 'all' and self.active_filters:
            stem += '_filtered'

        if file_format == 'csv':
            # utf-8-sig so Excel opens non-ASCII text correctly.
            payload = frame.to_csv(index=False).encode('utf-8-sig')
            return payload, f'{stem}.csv', 'text/csv'

        if file_format == 'xlsx':
            if len(frame) >= EXCEL_MAX_ROWS:
                raise DataError('Too many rows for an Excel sheet; export as CSV instead')
            buffer = BytesIO()
            try:
                frame.to_excel(buffer, index=False, sheet_name='Data')
            except Exception as exc:
                raise DataError(f'Could not write Excel file ({exc}); export as CSV instead')
            return (buffer.getvalue(), f'{stem}.xlsx',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        raise DataError('Export format must be "csv" or "xlsx"')

    # -- state summary ------------------------------------------------------

    def state(self):
        """Everything the frontend needs to (re)build its view of the dataset."""
        return {
            'columns': list(self.original_data.columns),
            'column_info': self.column_info,
            'shape': [len(self.original_data), self.original_data.shape[1]],
            'file_name': self.file_name,
            'sheet_names': self.sheet_names,
            'active_sheet': self.active_sheet,
            **self.filter_status(),
        }

    def filter_status(self):
        return {
            'has_filters': len(self.active_filters) > 0,
            'active_filters': self.active_filters,
            'filtered_rows': len(self.data),
            'total_rows': len(self.original_data),
        }

    # -- profiling ----------------------------------------------------------

    def profile(self):
        """Summary statistics and data-quality alerts for the filtered data."""
        frame = self.data
        rows = len(frame)
        alerts, columns = [], []

        def alert(severity, column, kind, message):
            alerts.append({'severity': severity, 'column': column, 'kind': kind, 'message': message})

        for name in frame.columns:
            series = frame[name]
            col_type = self.column_info.get(name, {}).get('type', 'text')
            non_null = series.dropna()
            missing = rows - len(non_null)
            missing_pct = round(100 * missing / rows, 2) if rows else 0
            unique = self._count_unique(non_null)
            entry = {'name': name, 'type': col_type, 'count': len(non_null), 'missing': missing,
                     'missing_pct': missing_pct, 'unique': unique}

            if rows and not len(non_null):
                alert('warning', name, 'empty', f'{name}: column is empty')
            elif missing_pct >= MISSING_WARNING_PCT:
                alert('warning', name, 'missing', f'{name}: {missing_pct}% of values are missing')
            elif missing_pct >= MISSING_INFO_PCT:
                alert('info', name, 'missing', f'{name}: {missing_pct}% of values are missing')
            if len(non_null) > 1 and unique == 1:
                alert('warning', name, 'constant', f'{name}: every value is the same ({non_null.iloc[0]})')

            if col_type == 'numeric':
                self._profile_numeric(entry, non_null, alert)
            elif col_type == 'datetime':
                self._profile_datetime(entry, non_null)
            elif col_type in ('categorical', 'text', 'boolean'):
                self._profile_discrete(entry, non_null, alert)
            columns.append(entry)

        duplicate_rows = None
        if rows:
            try:
                duplicate_rows = int(frame.duplicated().sum())
            except TypeError:
                duplicate_rows = int(frame.astype(str).duplicated().sum())
            if duplicate_rows:
                alert('info', None, 'duplicates',
                      f'{duplicate_rows:,} duplicate rows ({round(100 * duplicate_rows / rows, 1)}%)')

        correlations = self._correlation_pairs(frame)
        for pair in correlations:
            if abs(pair['r']) >= HIGH_CORRELATION:
                alert('info', pair['a'], 'high_correlation',
                      f'{pair["a"]} and {pair["b"]} are highly correlated (r = {pair["r"]:.2f})')

        cells = rows * frame.shape[1]
        missing_cells = int(frame.isna().sum().sum())
        type_counts = {}
        for entry in columns:
            type_counts[entry['type']] = type_counts.get(entry['type'], 0) + 1

        alerts.sort(key=lambda a: 0 if a['severity'] == 'warning' else 1)
        return {
            'overview': {
                'rows': rows,
                'total_rows': len(self.original_data),
                'columns': frame.shape[1],
                'missing_cells': missing_cells,
                'missing_pct': round(100 * missing_cells / cells, 2) if cells else 0,
                'duplicate_rows': duplicate_rows,
                'memory_bytes': int(frame.memory_usage(deep=True).sum()),
                'type_counts': type_counts,
                'has_filters': len(self.active_filters) > 0,
            },
            'alerts': alerts,
            'correlations': correlations,
            'columns': columns,
        }

    @staticmethod
    def _profile_numeric(entry, non_null, alert):
        values = pd.to_numeric(non_null, errors='coerce').astype(float)
        values = values[np.isfinite(values)]
        if values.empty:
            return
        name = entry['name']
        q1, median, q3 = (float(q) for q in values.quantile([0.25, 0.5, 0.75]))
        iqr = q3 - q1
        outliers = int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum()) if iqr > 0 else 0
        skew = float(values.skew()) if len(values) > 2 else None
        entry['stats'] = {
            'mean': _round(values.mean()), 'std': _round(values.std()) if len(values) > 1 else None,
            'min': _round(values.min()), 'q1': _round(q1), 'median': _round(median), 'q3': _round(q3),
            'max': _round(values.max()), 'skew': _round(skew), 'zeros': int((values == 0).sum()),
            'outliers': outliers,
        }
        bins = 1 if values.min() == values.max() else int(min(20, max(5, math.ceil(math.sqrt(len(values))))))
        counts, edges = np.histogram(values.to_numpy(), bins=bins)
        entry['histogram'] = {'counts': counts.tolist(), 'edges': [_round(e) for e in edges]}

        if outliers and outliers >= 0.01 * len(values):
            alert('info', name, 'outliers',
                  f'{name}: {outliers:,} outliers ({round(100 * outliers / len(values), 1)}%) by the 1.5×IQR rule')
        if skew is not None and math.isfinite(skew) and abs(skew) > SKEW_THRESHOLD:
            alert('info', name, 'skewed', f'{name}: distribution is highly skewed (skew = {skew:.1f})')
        if entry['unique'] == len(values) and len(values) > 10 and bool((values % 1 == 0).all()):
            alert('info', name, 'unique', f'{name}: every value is unique (possibly an ID column)')

    @staticmethod
    def _profile_datetime(entry, non_null):
        dates = pd.to_datetime(non_null, errors='coerce').dropna()
        if dates.empty:
            return
        low, high = dates.min(), dates.max()
        entry['stats'] = {'min': _format_timestamp(low), 'max': _format_timestamp(high),
                          'range_days': int((high - low).days)}
        if low != high:
            stamps = dates.astype('int64').to_numpy()
            counts, edges = np.histogram(stamps, bins=12)
            entry['histogram'] = {
                'counts': counts.tolist(),
                'edges': [pd.Timestamp(int(e)).strftime('%Y-%m-%d') for e in edges],
            }

    @staticmethod
    def _profile_discrete(entry, non_null, alert):
        if non_null.empty:
            return
        name, col_type = entry['name'], entry['type']
        text = non_null.astype(str)
        top = text.value_counts().head(5)
        entry['top_values'] = [
            {'value': value, 'count': int(count), 'pct': round(100 * count / len(text), 1)}
            for value, count in top.items()
        ]
        if col_type == 'text':
            lengths = text.str.len()
            entry['stats'] = {'min_length': int(lengths.min()), 'max_length': int(lengths.max()),
                              'avg_length': _round(lengths.mean(), 1)}
        if col_type == 'categorical' and entry['unique'] > HIGH_CARDINALITY:
            alert('info', name, 'high_cardinality',
                  f'{name}: {entry["unique"]:,} distinct categories (high cardinality)')
        if col_type in ('categorical', 'text') and non_null.dtype == object:
            numeric = pd.to_numeric(text.str.strip(), errors='coerce')
            share = float(numeric.notna().mean())
            if MOSTLY_NUMERIC_SHARE <= share < 1:
                bad = text[numeric.isna()]
                alert('warning', name, 'mixed_types',
                      f'{name}: looks numeric but {len(bad):,} values are not numbers (e.g. "{bad.iloc[0]}")')

    def _correlation_pairs(self, frame):
        numeric = [c for c in frame.columns
                   if self.column_info.get(c, {}).get('type') == 'numeric'][:MAX_CORRELATION_COLUMNS]
        if len(numeric) < 2 or len(frame) < 3:
            return []
        matrix = (frame[numeric].apply(pd.to_numeric, errors='coerce')
                  .replace([np.inf, -np.inf], np.nan).corr(min_periods=3))
        pairs = []
        for i, a in enumerate(numeric):
            for b in numeric[i + 1:]:
                r = matrix.loc[a, b]
                if pd.notna(r) and abs(r) >= CORRELATION_LIST_MIN:
                    pairs.append({'a': a, 'b': b, 'r': round(float(r), 3)})
        pairs.sort(key=lambda pair: -abs(pair['r']))
        return pairs[:20]

    # -- plotting -----------------------------------------------------------

    def build_figure(self, plot_config):
        """Plotly figure for ``plot_config``; raises PlotError with a reason."""
        return build_plot(self.data, self.column_info, plot_config)

    def generate_plot(self, plot_config):
        """Backwards-compatible: figure JSON string, or None if it cannot be built."""
        try:
            return figure_to_json(self.build_figure(plot_config))
        except PlotError as exc:
            print(f'Error generating plot: {exc}')
            return None
