import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Alert,
  Autocomplete,
  CircularProgress,
  TextField
} from '@mui/material';
import { BarChart, FilterList, AutoFixHigh, Refresh } from '@mui/icons-material';
import Plot from 'react-plotly.js';
import axios from 'axios';
import API_BASE_URL from '../config';

const NUMERIC = ['numeric'];
const CATEGORY = ['categorical', 'boolean'];
const ALL_TYPES = ['numeric', 'categorical', 'text', 'datetime', 'boolean'];

const AGGREGATIONS = ['mean', 'sum', 'median', 'min', 'max', 'count'];
const RESAMPLE_PERIODS = ['none', 'day', 'week', 'month', 'quarter', 'year'];

// Each plot type declares the column roles it needs ("fields") and which
// extra options apply. `columns` sent to the backend is the field values in
// this order.
const PLOT_TYPES = [
  {
    value: 'histogram', icon: '📊', label: 'Histogram',
    description: 'Distribution of one numeric column.',
    fields: [{ key: 'x', label: 'Column', types: NUMERIC, required: true }],
    options: ['color', 'bins'],
  },
  {
    value: 'box', icon: '📦', label: 'Box Plot',
    description: 'Median, quartiles and outliers, optionally per group.',
    fields: [
      { key: 'y', label: 'Values', types: NUMERIC, required: true },
      { key: 'group', label: 'Group by (optional)', types: CATEGORY },
    ],
    options: [],
  },
  {
    value: 'violin', icon: '🎻', label: 'Violin Plot',
    description: 'Distribution shape, optionally per group.',
    fields: [
      { key: 'y', label: 'Values', types: NUMERIC, required: true },
      { key: 'group', label: 'Group by (optional)', types: CATEGORY },
    ],
    options: [],
  },
  {
    value: 'bar', icon: '📈', label: 'Bar Chart',
    description: 'Counts per category. Add a second category to split the bars, or a numeric column to aggregate it per category.',
    fields: [
      { key: 'x', label: 'Category', types: CATEGORY, required: true },
      { key: 'second', label: 'Split by / value (optional)', types: [...CATEGORY, ...NUMERIC] },
    ],
    options: ['stacked', 'agg', 'top_n'],
  },
  {
    value: 'pie', icon: '🥧', label: 'Pie Chart',
    description: 'Share of each category. Small categories are grouped as "Other".',
    fields: [{ key: 'x', label: 'Category', types: CATEGORY, required: true }],
    options: ['top_n'],
  },
  {
    value: 'scatter', icon: '🔵', label: 'Scatter Plot',
    description: 'Relationship between two numeric columns.',
    fields: [
      { key: 'x', label: 'X axis', types: NUMERIC, required: true },
      { key: 'y', label: 'Y axis', types: NUMERIC, required: true },
    ],
    options: ['color', 'trendline'],
  },
  {
    value: 'line', icon: '📉', label: 'Line Chart',
    description: 'One or more numeric columns over a date or numeric x-axis. Dates can be grouped by period.',
    fields: [
      { key: 'x', label: 'X axis (date or number)', types: ['datetime', 'numeric'], required: true },
      { key: 'ys', label: 'Y values', types: NUMERIC, required: true, multiple: true, max: 5 },
    ],
    options: ['resample', 'agg'],
  },
  {
    value: 'heatmap', icon: '🌡️', label: 'Correlation Heatmap',
    description: 'Pairwise correlation between numeric columns. Leave the selection empty to use all of them.',
    fields: [{ key: 'cols', label: 'Columns (optional, default all numeric)', types: NUMERIC, multiple: true, max: 30 }],
    options: ['method'],
  },
  {
    value: 'llm', icon: '🤖', label: 'Custom Graph (AI)',
    description: 'Describe a plot in plain language. The model writes Plotly code that runs on this machine.',
    fields: [{ key: 'cols', label: 'Columns to focus on (optional)', types: ALL_TYPES, multiple: true }],
    options: [],
  },
];

const asList = (value) => (Array.isArray(value) ? value : value ? [value] : []);

const PlotGenerator = ({ data, columnInfo, refreshKey, onError }) => {
  const [plotType, setPlotType] = useState('');
  const [fieldValues, setFieldValues] = useState({});
  const [plotOptions, setPlotOptions] = useState({});
  const [plotData, setPlotData] = useState(null);
  // refreshKey at the time the current plot was drawn, to flag stale plots.
  const [plotVersion, setPlotVersion] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [llmPrompt, setLlmPrompt] = useState('');
  const [llmModel, setLlmModel] = useState('gemini');
  const [errorMessage, setErrorMessage] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');

  const currentType = PLOT_TYPES.find((type) => type.value === plotType);

  const columnsOfTypes = (types) =>
    Object.entries(columnInfo)
      .filter(([, info]) => types.includes(info.type))
      .map(([column]) => column);

  // Drop selections whose column vanished or changed type (new file, sheet
  // switch, type override) instead of sending a stale name to the backend.
  const validValue = (field) => {
    const allowed = columnsOfTypes(field.types);
    const kept = asList(fieldValues[field.key]).filter((column) => allowed.includes(column));
    return field.multiple ? kept : (kept[0] || null);
  };

  const typeOf = (column) => columnInfo[column]?.type;
  const colorColumn = plotOptions.color && CATEGORY.includes(typeOf(plotOptions.color)) ? plotOptions.color : null;

  const buildConfig = () => {
    const columns = currentType.fields.flatMap((field) => asList(validValue(field)));
    const config = { type: plotType, columns };
    const has = (option) => currentType.options.includes(option);
    const second = plotType === 'bar' ? validValue(currentType.fields[1]) : null;
    const xType = plotType === 'line' ? typeOf(validValue(currentType.fields[0])) : null;

    if (has('color') && colorColumn) config.color = colorColumn;
    if (has('bins') && plotOptions.bins) config.bins = Number(plotOptions.bins);
    if (has('trendline') && plotOptions.trendline) config.trendline = true;
    if (has('top_n') && plotOptions.top_n) config.top_n = Number(plotOptions.top_n);
    if (has('method')) config.method = plotOptions.method || 'pearson';
    if (has('stacked') && second && CATEGORY.includes(typeOf(second))) config.stacked = Boolean(plotOptions.stacked);
    if (plotType === 'bar' && second && typeOf(second) === 'numeric') config.agg = plotOptions.agg || 'mean';
    if (plotType === 'line') {
      config.agg = plotOptions.agg || 'mean';
      if (xType === 'datetime' && plotOptions.resample && plotOptions.resample !== 'none') {
        config.resample = plotOptions.resample;
      }
    }
    return config;
  };

  const canGeneratePlot = () => {
    if (!currentType) return false;
    if (plotType === 'llm') return llmPrompt.trim() !== '';
    return currentType.fields.every((field) => !field.required || asList(validValue(field)).length > 0);
  };

  const generatePlot = async () => {
    if (!canGeneratePlot()) return;

    setIsGenerating(true);
    try {
      const response = plotType === 'llm'
        ? await axios.post(`${API_BASE_URL}/generate-llm-plot`, {
          prompt: llmPrompt,
          columns: validValue(currentType.fields[0]),
          model: llmModel,
        })
        : await axios.post(`${API_BASE_URL}/plot`, buildConfig());

      setPlotData(JSON.parse(response.data.plot));
      setPlotVersion(refreshKey);
      setGeneratedCode(response.data.generated_code || '');
      setErrorMessage('');
    } catch (error) {
      let message;
      if (error.response) {
        message = error.response.data?.error || `Backend error (${error.response.status})`;
      } else if (error.request) {
        message = `Cannot reach the backend at ${API_BASE_URL}`;
      } else {
        message = `Could not read the plot: ${error.message}`;
      }
      setErrorMessage(message);
      setGeneratedCode(error.response?.data?.generated_code || '');
      onError(message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePlotTypeChange = (newType) => {
    setPlotType(newType);
    setFieldValues({});
    setPlotOptions({});
    setPlotData(null);
    setPlotVersion(null);
    setErrorMessage('');
    setGeneratedCode('');
  };

  const setField = (key, value) => {
    setFieldValues((previous) => ({ ...previous, [key]: value }));
    setErrorMessage('');
  };

  const setOption = (key, value) => setPlotOptions((previous) => ({ ...previous, [key]: value }));

  const renderField = (field) => {
    const options = columnsOfTypes(field.types);
    const value = validValue(field);
    return (
      <Autocomplete
        key={field.key}
        multiple={Boolean(field.multiple)}
        options={options}
        value={value}
        onChange={(event, newValue) => {
          if (field.multiple && field.max && newValue.length > field.max) return;
          setField(field.key, newValue);
        }}
        groupBy={field.types.length > 1 ? (option) => typeOf(option) : undefined}
        disableCloseOnSelect={Boolean(field.multiple)}
        size="small"
        noOptionsText={`No ${field.types.join(' / ')} columns`}
        renderInput={(params) => (
          <TextField
            {...params}
            label={field.label}
            required={Boolean(field.required)}
            helperText={options.length === 0 ? `No ${field.types.join(' / ')} columns in this dataset` : undefined}
          />
        )}
        sx={{ mb: 2 }}
      />
    );
  };

  const renderOptions = () => {
    if (!currentType) return null;
    const has = (option) => currentType.options.includes(option);
    const second = plotType === 'bar' ? validValue(currentType.fields[1]) : null;
    const secondType = second ? typeOf(second) : null;
    const xIsDate = plotType === 'line' && typeOf(validValue(currentType.fields[0])) === 'datetime';
    const showAgg = (plotType === 'bar' && secondType === 'numeric') || plotType === 'line';

    return (
      <>
        {has('color') && (
          <Autocomplete
            options={columnsOfTypes(CATEGORY)}
            value={colorColumn}
            onChange={(event, newValue) => setOption('color', newValue)}
            size="small"
            renderInput={(params) => <TextField {...params} label="Colour by (optional)" />}
            sx={{ mb: 2 }}
          />
        )}

        {has('resample') && xIsDate && (
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel id="resample-label">Group dates by</InputLabel>
            <Select
              labelId="resample-label"
              label="Group dates by"
              value={plotOptions.resample || 'none'}
              onChange={(event) => setOption('resample', event.target.value)}
            >
              {RESAMPLE_PERIODS.map((period) => (
                <MenuItem key={period} value={period}>{period === 'none' ? 'No grouping' : period}</MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        {has('agg') && showAgg && (
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel id="agg-label">Aggregation</InputLabel>
            <Select
              labelId="agg-label"
              label="Aggregation"
              value={plotOptions.agg || 'mean'}
              onChange={(event) => setOption('agg', event.target.value)}
            >
              {AGGREGATIONS.map((agg) => (
                <MenuItem key={agg} value={agg}>{agg}</MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        {has('method') && (
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel id="method-label">Method</InputLabel>
            <Select
              labelId="method-label"
              label="Method"
              value={plotOptions.method || 'pearson'}
              onChange={(event) => setOption('method', event.target.value)}
            >
              <MenuItem value="pearson">Pearson (linear)</MenuItem>
              <MenuItem value="spearman">Spearman (rank)</MenuItem>
            </Select>
          </FormControl>
        )}

        {has('bins') && (
          <TextField
            fullWidth
            size="small"
            type="number"
            label="Number of bins (optional)"
            value={plotOptions.bins || ''}
            onChange={(event) => setOption('bins', event.target.value)}
            inputProps={{ min: 1, max: 500 }}
            sx={{ mb: 2 }}
          />
        )}

        {has('top_n') && (
          <TextField
            fullWidth
            size="small"
            type="number"
            label={plotType === 'pie' ? 'Slices before "Other" (default 10)' : 'Show only top N categories (optional)'}
            value={plotOptions.top_n || ''}
            onChange={(event) => setOption('top_n', event.target.value)}
            inputProps={{ min: 1 }}
            sx={{ mb: 2 }}
          />
        )}

        {has('stacked') && secondType && CATEGORY.includes(secondType) && (
          <FormControlLabel
            control={
              <Switch
                checked={plotOptions.stacked || false}
                onChange={(event) => setOption('stacked', event.target.checked)}
              />
            }
            label="Stacked Bar Chart"
          />
        )}

        {has('trendline') && (
          <FormControlLabel
            control={
              <Switch
                checked={plotOptions.trendline || false}
                onChange={(event) => setOption('trendline', event.target.checked)}
              />
            }
            label="Linear trendline"
          />
        )}
      </>
    );
  };

  const isStale = plotData && plotVersion !== null && plotVersion !== refreshKey;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h5">
          Plot Generator
        </Typography>
        {data.has_filters && (
          <Alert severity="info" icon={<FilterList />} sx={{ py: 0 }}>
            Filters active: {data.filtered_rows.toLocaleString()} / {data.total_rows.toLocaleString()} rows
          </Alert>
        )}
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Plot Configuration
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel id="plot-type-label">Plot Type</InputLabel>
                <Select
                  labelId="plot-type-label"
                  value={plotType}
                  label="Plot Type"
                  onChange={(e) => handlePlotTypeChange(e.target.value)}
                >
                  {PLOT_TYPES.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.icon} {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {currentType && (
                <Box>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    {currentType.description}
                  </Alert>

                  {plotType === 'llm' && (
                    <>
                      <TextField
                        fullWidth
                        multiline
                        rows={4}
                        label="Describe the plot you want"
                        value={llmPrompt}
                        onChange={(e) => setLlmPrompt(e.target.value)}
                        sx={{ mb: 2 }}
                      />
                      <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                        <InputLabel id="llm-model-label">AI Model</InputLabel>
                        <Select
                          labelId="llm-model-label"
                          value={llmModel}
                          label="AI Model"
                          onChange={(e) => setLlmModel(e.target.value)}
                        >
                          <MenuItem value="gemini">Gemini 2.5 Flash (needs GEMINI_API_KEY)</MenuItem>
                          <MenuItem value="test">Test Model (offline)</MenuItem>
                        </Select>
                      </FormControl>
                    </>
                  )}

                  {currentType.fields.map(renderField)}
                  {renderOptions()}

                  <Button
                    fullWidth
                    variant="contained"
                    onClick={generatePlot}
                    disabled={!canGeneratePlot() || isGenerating}
                    startIcon={isGenerating ? <CircularProgress size={20} /> : (plotType === 'llm' ? <AutoFixHigh /> : <BarChart />)}
                    sx={{ mt: 2 }}
                  >
                    {isGenerating ? 'Generating...' : 'Generate Plot'}
                  </Button>

                  {errorMessage && (
                    <Alert severity="error" sx={{ mt: 2 }} data-testid="plot-error">
                      {errorMessage}
                    </Alert>
                  )}

                  {generatedCode && (
                    <Box component="details" sx={{ mt: 2 }}>
                      <Typography component="summary" variant="body2" sx={{ cursor: 'pointer' }}>
                        Generated code
                      </Typography>
                      <Box
                        component="pre"
                        sx={{ fontSize: '0.75rem', overflowX: 'auto', p: 1, backgroundColor: '#f5f5f5', borderRadius: 1 }}
                      >
                        {generatedCode}
                      </Box>
                    </Box>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Visualization
              </Typography>

              {isStale && (
                <Alert
                  severity="warning"
                  sx={{ mb: 1 }}
                  action={
                    <Button color="inherit" size="small" startIcon={<Refresh />} onClick={generatePlot} disabled={isGenerating}>
                      Regenerate
                    </Button>
                  }
                >
                  The data or filters changed after this plot was drawn.
                </Alert>
              )}

              {plotData ? (
                <Box data-testid="plot-container">
                  <Plot
                    data={plotData.data}
                    layout={{
                      ...plotData.layout,
                      autosize: true,
                      margin: { t: 60, r: 30, b: 50, l: 60 },
                      xaxis: { ...plotData.layout?.xaxis, automargin: true },
                      yaxis: { ...plotData.layout?.yaxis, automargin: true },
                    }}
                    config={{
                      responsive: true,
                      displaylogo: false,
                      toImageButtonOptions: { filename: `${plotType || 'plot'}`, scale: 2 },
                    }}
                    style={{ width: '100%', height: '500px' }}
                    useResizeHandler={true}
                  />
                </Box>
              ) : (
                <Box
                  sx={{
                    height: 400,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: '#f5f5f5',
                    borderRadius: 1,
                    border: '2px dashed #ccc'
                  }}
                >
                  <Typography color="text.secondary">
                    {plotType
                      ? 'Configure your plot and click "Generate Plot"'
                      : 'Select a plot type to get started'}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PlotGenerator;
