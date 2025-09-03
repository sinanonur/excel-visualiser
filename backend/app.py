from flask import Flask, request, jsonify
from flask_cors import CORS
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
    
    def load_excel(self, file_content):
        try:
            self.data = pd.read_excel(BytesIO(file_content))
            self.original_data = self.data.copy()
            self.detect_column_types()
            return True
        except Exception as e:
            print(f"Error loading Excel: {e}")
            return False
    
    def detect_column_types(self):
        self.column_info = {}
        for col in self.data.columns:
            col_data = self.data[col].dropna()
            if len(col_data) == 0:
                self.column_info[col] = {'type': 'empty', 'has_lists': False}
                continue
            
            has_lists = self.detect_lists_or_sets(col_data)
            
            if col_data.dtype in ['int64', 'float64']:
                col_type = 'numeric'
            elif col_data.dtype == 'bool':
                col_type = 'boolean'
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                col_type = 'datetime'
            else:
                unique_ratio = len(col_data.unique()) / len(col_data)
                if unique_ratio < 0.1 or len(col_data.unique()) < 20:
                    col_type = 'categorical'
                else:
                    col_type = 'text'
            
            self.column_info[col] = {
                'type': col_type,
                'has_lists': has_lists,
                'unique_values': len(col_data.unique()),
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
            return True
            
        except Exception as e:
            print(f"Error applying filters: {e}")
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
            
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            
        except Exception as e:
            print(f"Error generating plot: {e}")
            return None

data_processor = DataProcessor()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'File must be an Excel file (.xlsx or .xls)'}), 400
    
    file_content = file.read()
    if data_processor.load_excel(file_content):
        response_data = {
            'success': True,
            'columns': list(data_processor.data.columns),
            'column_info': data_processor.column_info,
            'shape': data_processor.data.shape,
            'preview': data_processor.data.head(10).to_dict('records')
        }
        # Convert to JSON serializable format
        response_data = convert_to_json_serializable(response_data)
        return jsonify(response_data)
    else:
        return jsonify({'error': 'Failed to process Excel file'}), 500

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
    data = request.json
    column = data.get('column')
    new_type = data.get('type')
    
    if not column or not new_type:
        return jsonify({'error': 'Column and type required'}), 400
    
    if column not in data_processor.data.columns:
        return jsonify({'error': 'Column not found'}), 400
    
    data_processor.column_info[column]['type'] = new_type
    return jsonify({'success': True})

@app.route('/expand-column', methods=['POST'])
def expand_column():
    data = request.json
    column = data.get('column')
    
    if not column:
        return jsonify({'error': 'Column required'}), 400
    
    if data_processor.expand_list_column(column):
        response_data = {
            'success': True,
            'columns': list(data_processor.data.columns),
            'column_info': data_processor.column_info
        }
        return jsonify(convert_to_json_serializable(response_data))
    else:
        return jsonify({'error': 'Failed to expand column'}), 500

@app.route('/plot', methods=['POST'])
def generate_plot():
    if data_processor.data is None:
        return jsonify({'error': 'No data loaded'}), 400
    
    plot_config = request.json
    plot_data = data_processor.generate_plot(plot_config)
    
    if plot_data:
        return jsonify({'plot': plot_data})
    else:
        return jsonify({'error': 'Could not generate plot with the given configuration'}), 400

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
    
    filters = request.json.get('filters', {})
    
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
        return jsonify({'error': 'Failed to apply filters'}), 500

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)