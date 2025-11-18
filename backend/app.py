from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from marshmallow import Schema, fields, validate, ValidationError
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import plotly.utils
import json
import re
import ast
from io import BytesIO
import base64
import os
import shelve
import hashlib
from datetime import datetime, timedelta
import sys
import tempfile
import logging
from logging.handlers import RotatingFileHandler
sys.path.append(os.path.join(os.path.dirname(__file__)))
from llm import GeminiLlm, TestLlm

# Cache configuration - Cross-platform compatible
CACHE_DIR = os.path.join(tempfile.gettempdir(), "excel_visualizer_cache")
CACHE_FILE = "column_type_cache"
CACHE_TTL_DAYS = 2

# File upload limits
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Validation Schemas
class PlotConfigSchema(Schema):
    type = fields.Str(
        required=True,
        validate=validate.OneOf(['violin', 'histogram', 'box', 'bar', 'scatter'])
    )
    columns = fields.List(fields.Str(), required=True)
    stacked = fields.Bool(missing=False)

class UpdateColumnTypeSchema(Schema):
    column = fields.Str(required=True)
    type = fields.Str(
        required=True,
        validate=validate.OneOf(['numeric', 'categorical', 'text', 'datetime', 'boolean'])
    )

class ExpandColumnSchema(Schema):
    column = fields.Str(required=True)

class FilterConfigSchema(Schema):
    filters = fields.Dict(keys=fields.Str(), required=True)

class LLMPlotConfigSchema(Schema):
    prompt = fields.Str(required=True, validate=validate.Length(min=1, max=5000))
    columns = fields.List(fields.Str(), missing=[])
    model = fields.Str(missing='gemini', validate=validate.OneOf(['gemini', 'test']))

class ExportDataSchema(Schema):
    format = fields.Str(required=True, validate=validate.OneOf(['csv', 'excel']))

class ExportPlotSchema(Schema):
    plot_data = fields.Dict(required=True)
    format = fields.Str(required=True, validate=validate.OneOf(['png', 'svg', 'pdf']))
    width = fields.Int(missing=1200, validate=validate.Range(min=100, max=4000))
    height = fields.Int(missing=800, validate=validate.Range(min=100, max=4000))

# Logging configuration
def setup_logging():
    """Configure application logging with rotation"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(tempfile.gettempdir(), "excel_visualizer_logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)

    # File handler with rotation (10MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Initialize logging
logger = setup_logging()
logger.info("="*60)
logger.info("Excel Data Science Visualizer - Backend Starting")
logger.info(f"Cache directory: {CACHE_DIR}")
logger.info(f"Python version: {sys.version}")
logger.info("="*60)

def get_cache():
    """Opens and returns the cache shelf."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return shelve.open(os.path.join(CACHE_DIR, CACHE_FILE))

def cleanup_cache():
    """Removes expired entries from the cache."""
    with get_cache() as cache:
        expired_keys = [
            key for key, value in cache.items()
            if datetime.now() - value['timestamp'] > timedelta(days=CACHE_TTL_DAYS)
        ]
        for key in expired_keys:
            del cache[key]

def convert_to_json_serializable(obj):
    """Convert pandas/numpy data types to JSON serializable types"""
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_json_serializable(item) for item in obj)
    elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

app = Flask(__name__)
CORS(app)

class DataProcessor:
    def __init__(self):
        self.data = None
        self.original_data = None
        self.filtered_data = None
        self.column_info = {}
        self.active_filters = {}
        self.file_hash = None
    
    def load_excel(self, file_content):
        try:
            self.data = pd.read_excel(BytesIO(file_content))
            self.original_data = self.data.copy()
            logger.info(f"Successfully loaded Excel file with shape {self.data.shape}")
            self.detect_column_types()
            return True
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}", exc_info=True)
            return False
    
    def detect_column_types(self):
        self.column_info = {}
        for col in self.data.columns:
            col_data = self.data[col]
            col_data_non_null = col_data.dropna()

            if len(col_data_non_null) == 0:
                self.column_info[col] = {'type': 'empty', 'has_lists': False, 'unique_values': 0, 'null_count': int(self.data[col].isna().sum())}
                continue

            has_lists = self.detect_lists_or_sets(col_data_non_null)
            
            # Default to text
            col_type = 'text'

            # Check for numeric types (native or convertible)
            if col_data_non_null.dtype in ['int64', 'float64']:
                col_type = 'numeric'
            elif col_data_non_null.dtype == 'object':
                # Attempt to convert to numeric
                numeric_series = pd.to_numeric(col_data_non_null, errors='coerce')
                # If all non-null values were converted to numbers, it's numeric
                if not numeric_series.isnull().any():
                    self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
                    col_type = 'numeric'

            # If not determined to be numeric, check other types
            if col_type != 'numeric':
                if col_data_non_null.dtype == 'bool':
                    col_type = 'boolean'
                elif pd.api.types.is_datetime64_any_dtype(col_data_non_null):
                    col_type = 'datetime'
                else: # It's a text-like column, let's see if it's categorical
                    num_unique = len(col_data_non_null.unique())
                    total_rows = len(self.data)

                    if num_unique < 4:
                        col_type = 'categorical'
                    elif (num_unique / total_rows) < 0.1:
                        col_type = 'categorical'
                    else:
                        col_type = 'text'
            
            self.column_info[col] = {
                'type': col_type,
                'has_lists': has_lists,
                'unique_values': len(col_data_non_null.unique()),
                'null_count': self.data[col].isna().sum()
            }
    
    def detect_lists_or_sets(self, series):
        sample_size = min(100, len(series))
        sample = series.head(sample_size).astype(str)
        
        list_pattern = r'^\s*\[.*\]\s*$'
        set_pattern = r'^\s*\{.*\}\s*$'
        
        list_matches = sum(1 for x in sample if re.match(list_pattern, x))
        set_matches = sum(1 for x in sample if re.match(set_pattern, x))
        
        return (list_matches + set_matches) > sample_size * 0.3
    
    def expand_list_column(self, column_name):
        if column_name not in self.data.columns:
            return False
        
        expanded_data = []
        for idx, value in self.data[column_name].items():
            if pd.isna(value):
                expanded_data.append([])
                continue
            
            try:
                str_val = str(value).strip()
                if str_val.startswith('[') and str_val.endswith(']'):
                    parsed = ast.literal_eval(str_val)
                    expanded_data.append(parsed if isinstance(parsed, list) else [parsed])
                elif str_val.startswith('{') and str_val.endswith('}'):
                    parsed = ast.literal_eval(str_val)
                    expanded_data.append(list(parsed) if isinstance(parsed, (set, frozenset)) else [parsed])
                else:
                    expanded_data.append([str_val])
            except:
                expanded_data.append([str(value)])
        
        max_len = max(len(items) for items in expanded_data) if expanded_data else 0
        
        for i in range(max_len):
            new_col_name = f"{column_name}_item_{i+1}"
            self.data[new_col_name] = [items[i] if i < len(items) else None for items in expanded_data]
        
        self.detect_column_types()
        return True
    
    def apply_filters(self, filters):
        """Apply filters to the data and store filtered result"""
        try:
            logger.info(f"Applying {len(filters)} filter(s)")
            self.active_filters = filters
            filtered_data = self.original_data.copy()

            for column, filter_config in filters.items():
                if column not in filtered_data.columns:
                    continue
                
                filter_type = filter_config.get('type')
                
                if filter_type == 'categorical':
                    # Filter by selected categories
                    selected_values = filter_config.get('values', [])
                    if selected_values:
                        filtered_data = filtered_data[filtered_data[column].isin(selected_values)]
                
                elif filter_type == 'numeric':
                    # Filter by numeric ranges
                    min_val = filter_config.get('min')
                    max_val = filter_config.get('max')
                    
                    if min_val is not None:
                        filtered_data = filtered_data[filtered_data[column] >= min_val]
                    if max_val is not None:
                        filtered_data = filtered_data[filtered_data[column] <= max_val]
                
                elif filter_type == 'text':
                    # Filter by text contains or regex
                    search_type = filter_config.get('search_type', 'contains')  # 'contains' or 'regex'
                    search_value = filter_config.get('value', '')
                    case_sensitive = filter_config.get('case_sensitive', False)
                    
                    if search_value:
                        if search_type == 'contains':
                            if case_sensitive:
                                mask = filtered_data[column].astype(str).str.contains(search_value, na=False)
                            else:
                                mask = filtered_data[column].astype(str).str.contains(search_value, case=False, na=False)
                        elif search_type == 'regex':
                            try:
                                if case_sensitive:
                                    mask = filtered_data[column].astype(str).str.contains(search_value, regex=True, na=False)
                                else:
                                    mask = filtered_data[column].astype(str).str.contains(search_value, case=False, regex=True, na=False)
                            except re.error:
                                # Invalid regex, skip this filter
                                continue
                        
                        filtered_data = filtered_data[mask]
                
                elif filter_type == 'boolean':
                    # Filter by boolean value
                    bool_value = filter_config.get('value')
                    if bool_value is not None:
                        filtered_data = filtered_data[filtered_data[column] == bool_value]
            
            self.filtered_data = filtered_data
            # Update current working data for plots
            self.data = filtered_data.copy()
            logger.info(f"Filters applied successfully. Result: {len(self.data)} rows (from {len(self.original_data)})")
            return True

        except Exception as e:
            logger.error(f"Error applying filters: {e}", exc_info=True)
            return False
    
    def clear_filters(self):
        """Clear all filters and restore original data"""
        self.active_filters = {}
        self.filtered_data = None
        self.data = self.original_data.copy()
    
    def get_filter_options(self, column):
        """Get available filter options for a column"""
        if column not in self.original_data.columns:
            return None
        
        col_info = self.column_info.get(column, {})
        col_type = col_info.get('type')
        
        if col_type == 'categorical':
            # Return unique values for categorical columns
            unique_values = self.original_data[column].dropna().unique().tolist()
            return {
                'type': 'categorical',
                'values': sorted([str(v) for v in unique_values])
            }
        
        elif col_type == 'numeric':
            # Return min/max for numeric columns
            col_data = self.original_data[column].dropna()
            return {
                'type': 'numeric',
                'min': float(col_data.min()),
                'max': float(col_data.max()),
                'mean': float(col_data.mean()),
                'std': float(col_data.std())
            }
        
        elif col_type == 'text':
            # Return text filter options
            return {
                'type': 'text',
                'sample_values': self.original_data[column].dropna().head(10).tolist()
            }
        
        elif col_type == 'boolean':
            # Return boolean options
            unique_values = self.original_data[column].dropna().unique().tolist()
            return {
                'type': 'boolean',
                'values': sorted([bool(v) for v in unique_values])
            }
        
        return None
    
    def generate_plot(self, plot_config):
        try:
            plot_type = plot_config['type']
            columns = plot_config['columns']
            
            if plot_type == 'violin':
                if len(columns) != 1:
                    return None
                col = columns[0]
                if self.column_info[col]['type'] != 'numeric':
                    return None
                
                fig = go.Figure(data=go.Violin(y=self.data[col].dropna(), name=col))
                fig.update_layout(title=f'Violin Plot of {col}')
                
            elif plot_type == 'bar':
                if len(columns) == 1:
                    col = columns[0]
                    if self.column_info[col]['type'] == 'categorical':
                        value_counts = self.data[col].value_counts()
                        fig = go.Figure(data=go.Bar(x=value_counts.index, y=value_counts.values))
                        fig.update_layout(title=f'Bar Chart of {col}')
                    else:
                        return None
                        
                elif len(columns) == 2:
                    col1, col2 = columns
                    if self.column_info[col1]['type'] == 'categorical' and self.column_info[col2]['type'] == 'categorical':
                        cross_tab = pd.crosstab(self.data[col1], self.data[col2])
                        
                        if plot_config.get('stacked', False):
                            fig = go.Figure()
                            for col in cross_tab.columns:
                                fig.add_trace(go.Bar(
                                    name=str(col),
                                    x=cross_tab.index,
                                    y=cross_tab[col]
                                ))
                            fig.update_layout(barmode='stack', title=f'Stacked Bar Chart: {col1} vs {col2}')
                        else:
                            fig = go.Figure()
                            for col in cross_tab.columns:
                                fig.add_trace(go.Bar(
                                    name=str(col),
                                    x=cross_tab.index,
                                    y=cross_tab[col]
                                ))
                            fig.update_layout(barmode='group', title=f'Grouped Bar Chart: {col1} vs {col2}')
                    else:
                        return None
                else:
                    return None
                    
            elif plot_type == 'scatter':
                if len(columns) != 2:
                    return None
                col1, col2 = columns
                if self.column_info[col1]['type'] == 'numeric' and self.column_info[col2]['type'] == 'numeric':
                    fig = go.Figure(data=go.Scatter(
                        x=self.data[col1],
                        y=self.data[col2],
                        mode='markers'
                    ))
                    fig.update_layout(title=f'Scatter Plot: {col1} vs {col2}')
                else:
                    return None
                    
            elif plot_type == 'histogram':
                if len(columns) != 1:
                    return None
                col = columns[0]
                if self.column_info[col]['type'] == 'numeric':
                    fig = go.Figure(data=go.Histogram(x=self.data[col].dropna()))
                    fig.update_layout(title=f'Histogram of {col}')
                else:
                    return None
                    
            elif plot_type == 'box':
                if len(columns) == 1:
                    col = columns[0]
                    if self.column_info[col]['type'] == 'numeric':
                        fig = go.Figure(data=go.Box(y=self.data[col].dropna(), name=col))
                        fig.update_layout(title=f'Box Plot of {col}')
                    else:
                        return None
                elif len(columns) == 2:
                    col1, col2 = columns
                    if self.column_info[col1]['type'] == 'numeric' and self.column_info[col2]['type'] == 'categorical':
                        fig = go.Figure()
                        for category in self.data[col2].unique():
                            if pd.notna(category):
                                data_subset = self.data[self.data[col2] == category][col1].dropna()
                                fig.add_trace(go.Box(y=data_subset, name=str(category)))
                        fig.update_layout(title=f'Box Plot: {col1} by {col2}')
                    else:
                        return None
                else:
                    return None
            else:
                return None
            
            logger.info(f"Successfully generated {plot_type} plot")
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        except Exception as e:
            logger.error(f"Error generating plot: {e}", exc_info=True)
            return None

data_processor = DataProcessor()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logger.warning("Upload attempt with no file")
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning("Upload attempt with empty filename")
        return jsonify({'error': 'No file selected'}), 400

    logger.info(f"File upload request: {file.filename}")

    if not file.filename.endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file format: {file.filename}")
        return jsonify({'error': 'File must be an Excel file (.xlsx or .xls)'}), 400

    # Read file content and check size
    file_content = file.read()
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE_BYTES:
        logger.warning(f"File too large: {file_size / (1024 * 1024):.2f}MB (max: {MAX_FILE_SIZE_MB}MB)")
        return jsonify({
            'error': f'File too large. Maximum size is {MAX_FILE_SIZE_MB}MB',
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'max_size_mb': MAX_FILE_SIZE_MB
        }), 413

    if file_size == 0:
        logger.warning("Empty file uploaded")
        return jsonify({'error': 'File is empty'}), 400

    logger.info(f"File size: {file_size / 1024:.2f}KB")

    file_hash = hashlib.sha256(file_content).hexdigest()
    data_processor.file_hash = file_hash

    if data_processor.load_excel(file_content):
        cleanup_cache()
        with get_cache() as cache:
            if file_hash in cache:
                # Load column types from cache
                data_processor.column_info = cache[file_hash]['column_info']
            else:
                # Store newly detected types in cache
                cache[file_hash] = {
                    'column_info': data_processor.column_info,
                    'timestamp': datetime.now()
                }

        response_data = {
            'success': True,
            'columns': list(data_processor.data.columns),
            'column_info': data_processor.column_info,
            'shape': data_processor.data.shape,
            'preview': data_processor.data.head(10).to_dict('records')
        }
        response_data = convert_to_json_serializable(response_data)
        logger.info(f"File upload successful: {file.filename}, shape: {data_processor.data.shape}")
        return jsonify(response_data)
    else:
        logger.error(f"Failed to process Excel file: {file.filename}")
        return jsonify({'error': 'Failed to process Excel file. Please ensure the file is a valid Excel file.'}), 500

@app.route('/column-info', methods=['GET'])
def get_column_info():
    if data_processor.data is None:
        return jsonify({'error': 'No data loaded'}), 400
    
    response_data = {
        'columns': list(data_processor.data.columns),
        'column_info': data_processor.column_info
    }
    return jsonify(convert_to_json_serializable(response_data))

@app.route('/update-column-type', methods=['POST'])
def update_column_type():
    # Validate input
    schema = UpdateColumnTypeSchema()
    try:
        validated_data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Invalid input', 'details': err.messages}), 400

    column = validated_data['column']
    new_type = validated_data['type']

    if column not in data_processor.data.columns:
        return jsonify({'error': f'Column "{column}" not found'}), 404

    data_processor.column_info[column]['type'] = new_type

    # Update the cache
    if data_processor.file_hash:
        with get_cache() as cache:
            if data_processor.file_hash in cache:
                cache[data_processor.file_hash] = {
                    'column_info': data_processor.column_info,
                    'timestamp': datetime.now()
                }

    return jsonify({'success': True, 'column': column, 'new_type': new_type})

@app.route('/expand-column', methods=['POST'])
def expand_column():
    # Validate input
    schema = ExpandColumnSchema()
    try:
        validated_data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Invalid input', 'details': err.messages}), 400

    column = validated_data['column']

    if column not in data_processor.data.columns:
        return jsonify({'error': f'Column "{column}" not found'}), 404

    if data_processor.expand_list_column(column):
        response_data = {
            'success': True,
            'columns': list(data_processor.data.columns),
            'column_info': data_processor.column_info
        }
        return jsonify(convert_to_json_serializable(response_data))
    else:
        return jsonify({'error': 'Failed to expand column. Please ensure it contains list or set values.'}), 500

@app.route('/plot', methods=['POST'])
def generate_plot():
    if data_processor.data is None:
        return jsonify({'error': 'No data loaded'}), 400

    # Validate input
    schema = PlotConfigSchema()
    try:
        validated_config = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Invalid plot configuration', 'details': err.messages}), 400

    # Validate that columns exist
    for col in validated_config['columns']:
        if col not in data_processor.data.columns:
            return jsonify({'error': f'Column "{col}" not found in dataset'}), 404

    plot_data = data_processor.generate_plot(validated_config)

    if plot_data:
        return jsonify({'plot': plot_data})
    else:
        return jsonify({'error': 'Could not generate plot with the given configuration. Please check column types and plot requirements.'}), 400

@app.route('/data-preview', methods=['GET'])
def get_data_preview():
    if data_processor.data is None:
        return jsonify({'error': 'No data loaded'}), 400
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    data_slice = data_processor.data.iloc[start_idx:end_idx]
    
    response_data = {
        'data': data_slice.to_dict('records'),
        'total_rows': len(data_processor.data),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(data_processor.data) + per_page - 1) // per_page
    }
    return jsonify(convert_to_json_serializable(response_data))

@app.route('/filter-options/<column>', methods=['GET'])
def get_filter_options(column):
    """Get available filter options for a specific column"""
    if data_processor.original_data is None:
        return jsonify({'error': 'No data loaded'}), 400
    
    filter_options = data_processor.get_filter_options(column)
    if filter_options is None:
        return jsonify({'error': 'Column not found'}), 404
    
    return jsonify(convert_to_json_serializable(filter_options))

@app.route('/apply-filters', methods=['POST'])
def apply_filters():
    """Apply filters to the dataset"""
    if data_processor.original_data is None:
        return jsonify({'error': 'No data loaded'}), 400

    # Validate input
    schema = FilterConfigSchema()
    try:
        validated_data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Invalid filter configuration', 'details': err.messages}), 400

    filters = validated_data['filters']

    if data_processor.apply_filters(filters):
        # Return updated statistics
        response_data = {
            'success': True,
            'filtered_rows': len(data_processor.data),
            'total_rows': len(data_processor.original_data),
            'active_filters': data_processor.active_filters
        }
        return jsonify(convert_to_json_serializable(response_data))
    else:
        return jsonify({'error': 'Failed to apply filters. Please check filter configuration.'}), 500

@app.route('/clear-filters', methods=['POST'])
def clear_filters():
    """Clear all filters and restore original data"""
    if data_processor.original_data is None:
        return jsonify({'error': 'No data loaded'}), 400
    
    data_processor.clear_filters()
    
    response_data = {
        'success': True,
        'total_rows': len(data_processor.data)
    }
    return jsonify(convert_to_json_serializable(response_data))

@app.route('/filter-status', methods=['GET'])
def get_filter_status():
    """Get current filter status and statistics"""
    if data_processor.original_data is None:
        return jsonify({'error': 'No data loaded'}), 400
    
    response_data = {
        'has_filters': len(data_processor.active_filters) > 0,
        'active_filters': data_processor.active_filters,
        'filtered_rows': len(data_processor.data),
        'total_rows': len(data_processor.original_data)
    }
    return jsonify(convert_to_json_serializable(response_data))

def safe_exec(code, local_vars):
    """Safely execute generated code."""
    allowed_globals = {
        'go': go,
        'px': px,
        'pd': pd,
        'np': np,
        'json': json,
        'plotly': plotly
    }
    try:
        logger.debug("Executing LLM-generated code in safe environment")
        logger.debug(f"Available globals: {list(allowed_globals.keys())}")
        logger.debug(f"Local vars before: {list(local_vars.keys())}")
        exec(code, allowed_globals, local_vars)
        logger.debug(f"Local vars after: {list(local_vars.keys())}")
        logger.info("LLM code execution completed successfully")
    except Exception as e:
        logger.error(f"Error executing LLM plot code: {type(e).__name__} - {e}")
        logger.error("Generated code:")
        for i, line in enumerate(code.split('\n'), 1):
            logger.error(f"  {i:3}: {line}")
        logger.error("Full traceback:", exc_info=True)
        raise

@app.route('/generate-llm-plot', methods=['POST'])
def generate_llm_plot():
    if data_processor.data is None:
        return jsonify({'error': 'No data loaded'}), 400

    # Validate input
    schema = LLMPlotConfigSchema()
    try:
        validated_config = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Invalid LLM plot configuration', 'details': err.messages}), 400

    prompt = validated_config['prompt']
    selected_columns = validated_config['columns']
    model = validated_config['model']

    try:
        logger.info(f"LLM Plot Request - Model: {model}, Prompt length: {len(prompt)} chars")
        logger.debug(f"Prompt preview: {prompt[:100]}...")

        if model == 'test':
            llm = TestLlm()
        else:
            llm = GeminiLlm()

        plot_code = llm.generate_plot_code(prompt, data_processor.data, selected_columns)
        logger.info(f"LLM generated {len(plot_code)} characters of code")
        logger.debug("Generated code:")
        logger.debug("="*50)
        logger.debug(plot_code)
        logger.debug("="*50)

        # Check if the code looks reasonable
        if not plot_code or len(plot_code.strip()) < 10:
            logger.warning("LLM generated empty or too short code")
            return jsonify({
                'error': 'LLM generated empty or too short code',
                'generated_code': plot_code
            }), 500

        local_vars = {'df': data_processor.data, 'fig': None}
        logger.debug(f"Executing code with df shape: {data_processor.data.shape}")
        safe_exec(plot_code, local_vars)

        fig = local_vars.get('fig')
        logger.debug(f"Fig object type: {type(fig)}")

        if fig:
            logger.info("LLM plot generated successfully")
            # Add validation of the fig object
            try:
                plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
                logger.debug(f"Plot JSON length: {len(plot_json)} characters")
                return jsonify({'plot': plot_json})
            except Exception as json_error:
                logger.error(f"Error converting fig to JSON: {json_error}")
                return jsonify({
                    'error': f'Error converting plot to JSON: {json_error}',
                    'generated_code': plot_code,
                    'fig_type': str(type(fig))
                }), 500
        else:
            logger.warning("No fig object created by LLM code")
            logger.debug(f"Available variables after execution: {list(local_vars.keys())}")
            return jsonify({
                'error': 'Could not generate plot from LLM response - no fig object created',
                'generated_code': plot_code,
                'available_vars': list(local_vars.keys())
            }), 500

    except Exception as e:
        error_msg = str(e)
        logger.error(f"LLM Plot Error: {error_msg}", exc_info=True)
        
        # Provide more detailed error information
        return jsonify({
            'error': f'Error generating plot: {error_msg}',
            'prompt': prompt,
            'model': model,
            'selected_columns': selected_columns,
            'available_columns': list(data_processor.data.columns) if data_processor.data is not None else []
        }), 500

@app.route('/export-data', methods=['POST'])
def export_data():
    """Export filtered or original data as CSV or Excel"""
    if data_processor.data is None:
        logger.warning("Export attempt with no data loaded")
        return jsonify({'error': 'No data loaded'}), 400

    # Validate input
    schema = ExportDataSchema()
    try:
        validated_data = schema.load(request.json)
    except ValidationError as err:
        logger.warning(f"Invalid export configuration: {err.messages}")
        return jsonify({'error': 'Invalid export configuration', 'details': err.messages}), 400

    export_format = validated_data['format']
    logger.info(f"Data export request: format={export_format}, rows={len(data_processor.data)}")

    try:
        # Use current data (filtered or original)
        df = data_processor.data.copy()

        # Create BytesIO buffer
        buffer = BytesIO()

        if export_format == 'csv':
            df.to_csv(buffer, index=False, encoding='utf-8')
            buffer.seek(0)
            mimetype = 'text/csv'
            filename = 'exported_data.csv'
        elif export_format == 'excel':
            df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = 'exported_data.xlsx'
        else:
            return jsonify({'error': 'Invalid export format'}), 400

        logger.info(f"Data exported successfully as {export_format}")
        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/export-plot', methods=['POST'])
def export_plot():
    """Export plot as static image (PNG, SVG, or PDF)"""
    # Validate input
    schema = ExportPlotSchema()
    try:
        validated_data = schema.load(request.json)
    except ValidationError as err:
        logger.warning(f"Invalid plot export configuration: {err.messages}")
        return jsonify({'error': 'Invalid export configuration', 'details': err.messages}), 400

    plot_data = validated_data['plot_data']
    export_format = validated_data['format']
    width = validated_data['width']
    height = validated_data['height']

    logger.info(f"Plot export request: format={export_format}, size={width}x{height}")

    try:
        # Reconstruct the figure from JSON
        fig = go.Figure(plot_data)

        # Export based on format
        buffer = BytesIO()

        if export_format == 'png':
            fig.write_image(buffer, format='png', width=width, height=height)
            buffer.seek(0)
            mimetype = 'image/png'
            filename = 'plot.png'
        elif export_format == 'svg':
            fig.write_image(buffer, format='svg', width=width, height=height)
            buffer.seek(0)
            mimetype = 'image/svg+xml'
            filename = 'plot.svg'
        elif export_format == 'pdf':
            fig.write_image(buffer, format='pdf', width=width, height=height)
            buffer.seek(0)
            mimetype = 'application/pdf'
            filename = 'plot.pdf'
        else:
            return jsonify({'error': 'Invalid export format'}), 400

        logger.info(f"Plot exported successfully as {export_format}")
        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Plot export failed: {e}", exc_info=True)
        return jsonify({
            'error': f'Plot export failed: {str(e)}',
            'hint': 'Make sure kaleido is installed: pip install kaleido'
        }), 500

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    app.run(host=host, debug=True, port=5001)