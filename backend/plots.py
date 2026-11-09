"""Plotly figure builders.

``build_plot(frame, column_info, config)`` returns a figure or raises
``PlotError`` with a message that tells the user what to change.

``config`` keys: ``type``, ``columns`` and, depending on the type, ``color``
(group-by column), ``stacked``, ``agg``, ``top_n``, ``bins``, ``trendline``,
``resample`` and ``method``.
"""

import json

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.utils

CATEGORY_TYPES = ('categorical', 'boolean')
AGGREGATIONS = ('mean', 'sum', 'median', 'min', 'max', 'count')
RESAMPLE_RULES = {'day': 'D', 'week': 'W', 'month': 'M', 'quarter': 'Q', 'year': 'Y'}
MAX_GROUPS = 30
MAX_LINE_SERIES = 5
MAX_HEATMAP_COLUMNS = 30
WEBGL_THRESHOLD = 5000


class PlotError(ValueError):
    """The requested plot cannot be drawn; the message says why."""


def figure_to_json(fig):
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def build_plot(frame, column_info, config):
    if not isinstance(config, dict):
        raise PlotError('Plot configuration must be an object')
    plot_type = config.get('type')
    builder = _BUILDERS.get(plot_type)
    if builder is None:
        raise PlotError(f'Unknown plot type "{plot_type}"')

    columns = config.get('columns') or []
    if not isinstance(columns, list):
        raise PlotError('"columns" must be a list of column names')
    referenced = list(columns) + ([config['color']] if config.get('color') else [])
    for col in referenced:
        if col not in frame.columns:
            raise PlotError(f'Column "{col}" does not exist')
    if len(frame) == 0:
        raise PlotError('No rows to plot. Check the active filters')

    context = _Context(frame, column_info, config, columns)
    fig = builder(context)
    fig.update_layout(template='plotly_white')
    return fig


class _Context:
    def __init__(self, frame, column_info, config, columns):
        self.frame = frame
        self.column_info = column_info
        self.config = config
        self.columns = columns

    def type_of(self, col):
        return self.column_info.get(col, {}).get('type')

    def is_numeric(self, col):
        return self.type_of(col) == 'numeric'

    def is_category(self, col):
        return self.type_of(col) in CATEGORY_TYPES

    def numeric(self, col):
        """Column as numbers; text and +/-infinity become missing."""
        return pd.to_numeric(self.frame[col], errors='coerce').replace([np.inf, -np.inf], np.nan)

    def expect_columns(self, low, high, what):
        count = len(self.columns)
        if not low <= count <= high:
            wanted = str(low) if low == high else f'{low}-{high}'
            raise PlotError(f'{what} needs {wanted} column(s); {count} selected')

    def split(self):
        """Selected columns partitioned into (numeric, category), any order."""
        numeric = [c for c in self.columns if self.is_numeric(c)]
        category = [c for c in self.columns if self.is_category(c)]
        other = [c for c in self.columns if c not in numeric and c not in category]
        if other:
            raise PlotError(
                f'"{other[0]}" is a {self.type_of(other[0])} column; this plot needs numeric or '
                'categorical columns (change the type under Column Management if it is wrong)')
        return numeric, category

    def color(self):
        """Validated group-by column, or None."""
        col = self.config.get('color')
        if not col:
            return None
        if not self.is_category(col):
            raise PlotError(f'Colour-by column "{col}" must be categorical or boolean')
        return col

    def groups(self, col):
        """Distinct non-null group labels of ``col``, capped for readability."""
        labels = self.frame[col].dropna().astype(str)
        values = sorted(labels.unique().tolist())
        if len(values) > MAX_GROUPS:
            raise PlotError(
                f'"{col}" has {len(values)} distinct values; pick a column with at most '
                f'{MAX_GROUPS} groups or filter the data first')
        return labels, values

    def aggregation(self):
        agg = self.config.get('agg') or 'mean'
        if agg not in AGGREGATIONS:
            raise PlotError(f'Aggregation must be one of: {", ".join(AGGREGATIONS)}')
        return agg

    def top_n(self, default=None):
        value = self.config.get('top_n', default)
        if value in (None, '', 0):
            return None
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise PlotError('"top_n" must be a whole number')
        if value < 1:
            raise PlotError('"top_n" must be at least 1')
        return value


def _require_numeric(ctx, col):
    if not ctx.is_numeric(col):
        raise PlotError(f'"{col}" must be a numeric column (it is {ctx.type_of(col)})')


def _distribution(ctx, trace_cls, title):
    """Shared shape of violin and box plots: one numeric, optional grouping."""
    ctx.expect_columns(1, 2, title)
    numeric, category = ctx.split()
    if len(numeric) != 1:
        raise PlotError(f'{title} needs exactly one numeric column (plus an optional categorical one)')
    value_col = numeric[0]
    group_col = category[0] if category else ctx.color()
    values = ctx.numeric(value_col)
    extra = {'box_visible': True, 'meanline_visible': True} if trace_cls is go.Violin else {}

    fig = go.Figure()
    if group_col:
        labels, groups = ctx.groups(group_col)
        for group in groups:
            subset = values[labels.index[labels == group]].dropna()
            if len(subset):
                fig.add_trace(trace_cls(y=subset, name=group, **extra))
        fig.update_layout(title=f'{title}: {value_col} by {group_col}', xaxis_title=group_col)
    else:
        fig.add_trace(trace_cls(y=values.dropna(), name=value_col, **extra))
        fig.update_layout(title=f'{title} of {value_col}')
    fig.update_layout(yaxis_title=value_col)
    return fig


def _violin(ctx):
    return _distribution(ctx, go.Violin, 'Violin Plot')


def _box(ctx):
    return _distribution(ctx, go.Box, 'Box Plot')


def _histogram(ctx):
    ctx.expect_columns(1, 1, 'Histogram')
    col = ctx.columns[0]
    _require_numeric(ctx, col)
    values = ctx.numeric(col)
    bins = ctx.config.get('bins')
    extra = {}
    if bins not in (None, ''):
        try:
            extra['nbinsx'] = max(1, min(int(bins), 500))
        except (TypeError, ValueError):
            raise PlotError('"bins" must be a whole number')

    fig = go.Figure()
    group_col = ctx.color()
    if group_col:
        labels, groups = ctx.groups(group_col)
        for group in groups:
            subset = values[labels.index[labels == group]].dropna()
            if len(subset):
                fig.add_trace(go.Histogram(x=subset, name=group, opacity=0.65, **extra))
        fig.update_layout(barmode='overlay', title=f'Histogram of {col} by {group_col}')
    else:
        fig.add_trace(go.Histogram(x=values.dropna(), name=col, **extra))
        fig.update_layout(title=f'Histogram of {col}')
    fig.update_layout(xaxis_title=col, yaxis_title='Count')
    return fig


def _bar(ctx):
    ctx.expect_columns(1, 2, 'Bar Chart')
    numeric, category = ctx.split()
    frame = ctx.frame
    top_n = ctx.top_n()

    if len(category) == 1 and not numeric:
        col = category[0]
        counts = frame[col].dropna().astype(str).value_counts()
        if top_n:
            counts = counts.head(top_n)
        fig = go.Figure(go.Bar(x=counts.index.tolist(), y=counts.values))
        fig.update_layout(title=f'Bar Chart of {col}', xaxis_title=col, yaxis_title='Count',
                          xaxis_type='category')
        return fig

    if len(category) == 2:
        first, second = ctx.columns
        ctx.groups(second)
        table = pd.crosstab(frame[first].astype(str).where(frame[first].notna()),
                            frame[second].astype(str).where(frame[second].notna()))
        if top_n:
            keep = table.sum(axis=1).sort_values(ascending=False).head(top_n).index
            table = table.loc[keep]
        stacked = bool(ctx.config.get('stacked', False))
        fig = go.Figure([go.Bar(name=str(level), x=table.index.tolist(), y=table[level])
                         for level in table.columns])
        fig.update_layout(barmode='stack' if stacked else 'group',
                          title=f'{"Stacked" if stacked else "Grouped"} Bar Chart: {first} vs {second}',
                          xaxis_title=first, yaxis_title='Count', legend_title=second,
                          xaxis_type='category')
        return fig

    if len(category) == 1 and len(numeric) == 1:
        cat_col, num_col = category[0], numeric[0]
        agg = ctx.aggregation()
        data = pd.DataFrame({'group': frame[cat_col].astype(str).where(frame[cat_col].notna()),
                             'value': ctx.numeric(num_col)}).dropna(subset=['group'])
        summary = data.groupby('group')['value'].agg(agg).dropna().sort_values(ascending=False)
        if top_n:
            summary = summary.head(top_n)
        if summary.empty:
            raise PlotError(f'No numeric values in "{num_col}" to aggregate')
        label = f'{agg.capitalize()} of {num_col}'
        fig = go.Figure(go.Bar(x=summary.index.tolist(), y=summary.values))
        fig.update_layout(title=f'{label} by {cat_col}', xaxis_title=cat_col,
                          yaxis_title=label, xaxis_type='category')
        return fig

    raise PlotError('Bar Chart needs one categorical column, two categorical columns, '
                    'or one categorical plus one numeric column')


def _scatter(ctx):
    ctx.expect_columns(2, 2, 'Scatter Plot')
    x_col, y_col = ctx.columns
    _require_numeric(ctx, x_col)
    _require_numeric(ctx, y_col)
    data = pd.DataFrame({'x': ctx.numeric(x_col), 'y': ctx.numeric(y_col)})
    group_col = ctx.color()
    if group_col:
        data['group'] = ctx.frame[group_col].astype(str).where(ctx.frame[group_col].notna())
    data = data.dropna(subset=['x', 'y'])
    if data.empty:
        raise PlotError(f'No rows have both "{x_col}" and "{y_col}"')

    trace_cls = go.Scattergl if len(data) > WEBGL_THRESHOLD else go.Scatter
    fig = go.Figure()
    if group_col:
        _, groups = ctx.groups(group_col)
        for group in groups:
            subset = data[data['group'] == group]
            if len(subset):
                fig.add_trace(trace_cls(x=subset['x'], y=subset['y'], mode='markers', name=group,
                                        marker={'opacity': 0.75}))
        fig.update_layout(legend_title=group_col)
    else:
        fig.add_trace(trace_cls(x=data['x'], y=data['y'], mode='markers', name='Data',
                                marker={'opacity': 0.75}))

    title = f'Scatter Plot: {x_col} vs {y_col}'
    if ctx.config.get('trendline'):
        if len(data) < 3 or data['x'].nunique() < 2:
            raise PlotError('A trendline needs at least 3 points with different x values')
        try:
            slope, intercept = np.polyfit(data['x'].to_numpy(float), data['y'].to_numpy(float), 1)
        except (np.linalg.LinAlgError, ValueError):
            raise PlotError('Could not fit a trendline to these values')
        r = data['x'].corr(data['y'])
        xs = np.array([data['x'].min(), data['x'].max()], dtype=float)
        r_squared = float(r) ** 2 if pd.notna(r) else float('nan')
        fig.add_trace(go.Scatter(
            x=xs, y=slope * xs + intercept, mode='lines',
            name=f'Linear fit (R² = {r_squared:.3f})', line={'dash': 'dash', 'color': '#444'}))
        if pd.notna(r):
            title += f' (r = {r:.3f})'
    fig.update_layout(title=title, xaxis_title=x_col, yaxis_title=y_col)
    return fig


def _line(ctx):
    ctx.expect_columns(2, 1 + MAX_LINE_SERIES, 'Line Chart')
    x_col, y_cols = ctx.columns[0], ctx.columns[1:]
    x_type = ctx.type_of(x_col)
    if x_type not in ('datetime', 'numeric'):
        raise PlotError(f'The x-axis column "{x_col}" must be a date or numeric column (it is {x_type})')
    for col in y_cols:
        _require_numeric(ctx, col)

    x_values = pd.to_datetime(ctx.frame[x_col], errors='coerce') if x_type == 'datetime' else ctx.numeric(x_col)
    data = pd.DataFrame({col: ctx.numeric(col) for col in y_cols})
    data.insert(0, '__x__', x_values)
    data = data.dropna(subset=['__x__']).sort_values('__x__', kind='stable')
    if data.empty:
        raise PlotError(f'"{x_col}" has no usable values')

    resample = ctx.config.get('resample')
    suffix = ''
    if resample and resample != 'none':
        if x_type != 'datetime':
            raise PlotError('Resampling by period needs a date column on the x-axis')
        if resample not in RESAMPLE_RULES:
            raise PlotError(f'Resample period must be one of: {", ".join(RESAMPLE_RULES)}')
        agg = ctx.aggregation()
        data = data.set_index('__x__').resample(RESAMPLE_RULES[resample]).agg(agg).reset_index()
        suffix = f' ({agg} per {resample})'
    elif data['__x__'].duplicated().any():
        # Several rows share an x value: aggregate so the line is a function of x.
        agg = ctx.aggregation()
        data = data.groupby('__x__', as_index=False).agg(agg)
        suffix = f' ({agg} per {x_col})'

    fig = go.Figure()
    for col in y_cols:
        series = data[['__x__', col]].dropna()
        fig.add_trace(go.Scatter(x=series['__x__'], y=series[col], mode='lines+markers', name=col))
    fig.update_layout(title=f'{", ".join(y_cols)} over {x_col}{suffix}', xaxis_title=x_col,
                      yaxis_title=y_cols[0] if len(y_cols) == 1 else 'Value')
    return fig


def _heatmap(ctx):
    columns = ctx.columns
    if not columns:
        columns = [c for c in ctx.frame.columns if ctx.is_numeric(c)][:MAX_HEATMAP_COLUMNS]
    for col in columns:
        _require_numeric(ctx, col)
    if len(columns) < 2:
        raise PlotError('A correlation heatmap needs at least two numeric columns')
    if len(columns) > MAX_HEATMAP_COLUMNS:
        raise PlotError(f'Select at most {MAX_HEATMAP_COLUMNS} columns for the heatmap')
    method = ctx.config.get('method') or 'pearson'
    if method not in ('pearson', 'spearman'):
        raise PlotError('Correlation method must be "pearson" or "spearman"')

    matrix = pd.DataFrame({col: ctx.numeric(col) for col in columns}).corr(method=method, min_periods=3)
    if matrix.isna().all().all():
        raise PlotError('Not enough overlapping numeric values to compute correlations')
    z = matrix.round(3).astype(object).where(matrix.notna(), None).values.tolist()
    fig = go.Figure(go.Heatmap(
        z=z, x=columns, y=columns, zmin=-1, zmax=1, colorscale='RdBu', reversescale=True,
        texttemplate='%{z:.2f}' if len(columns) <= 15 else None,
        hovertemplate='%{y} × %{x}<br>r = %{z:.3f}<extra></extra>',
        colorbar={'title': 'r'}))
    fig.update_layout(title=f'Correlation Heatmap ({method.capitalize()})',
                      yaxis={'autorange': 'reversed'})
    return fig


def _pie(ctx):
    ctx.expect_columns(1, 1, 'Pie Chart')
    col = ctx.columns[0]
    if not ctx.is_category(col):
        raise PlotError(f'"{col}" must be a categorical or boolean column (it is {ctx.type_of(col)})')
    counts = ctx.frame[col].dropna().astype(str).value_counts()
    if counts.empty:
        raise PlotError(f'"{col}" has no values')
    top_n = ctx.top_n(default=10)
    if top_n and len(counts) > top_n:
        other = counts.iloc[top_n:].sum()
        counts = counts.head(top_n)
        counts.loc['Other'] = other
    fig = go.Figure(go.Pie(labels=counts.index.tolist(), values=counts.values, hole=0.35, sort=False))
    fig.update_layout(title=f'Share of {col}')
    return fig


_BUILDERS = {
    'violin': _violin,
    'histogram': _histogram,
    'box': _box,
    'bar': _bar,
    'scatter': _scatter,
    'line': _line,
    'heatmap': _heatmap,
    'pie': _pie,
}
