import React, { useState, useEffect } from 'react';
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
  Chip,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress
} from '@mui/material';
import { BarChart, ScatterPlot, Timeline, FilterList } from '@mui/icons-material';
import Plot from 'react-plotly.js';
import axios from 'axios';
import API_BASE_URL from '../config';

const PlotGenerator = ({ data, columnInfo, onError }) => {
  const [plotType, setPlotType] = useState('');
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [plotOptions, setPlotOptions] = useState({});
  const [plotData, setPlotData] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [filterStatus, setFilterStatus] = useState({ has_filters: false, filtered_rows: 0, total_rows: 0 });

  useEffect(() => {
    loadFilterStatus();
  }, [data]);

  const loadFilterStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/filter-status`);
      setFilterStatus(response.data);
    } catch (error) {
      console.error('Error loading filter status:', error);
    }
  };

  const plotTypes = [
    { value: 'violin', label: '🎻 Violin Plot', description: 'Distribution shape for numeric data', minCols: 1, maxCols: 1, types: ['numeric'] },
    { value: 'histogram', label: '📊 Histogram', description: 'Distribution of numeric data', minCols: 1, maxCols: 1, types: ['numeric'] },
    { value: 'box', label: '📦 Box Plot', description: 'Statistical summary of numeric data', minCols: 1, maxCols: 2, types: ['numeric', 'categorical'] },
    { value: 'bar', label: '📈 Bar Chart', description: 'Categorical data visualization', minCols: 1, maxCols: 2, types: ['categorical'] },
    { value: 'scatter', label: '🔵 Scatter Plot', description: 'Relationship between two numeric variables', minCols: 2, maxCols: 2, types: ['numeric'] }
  ];

  const getAvailableColumns = (requiredTypes) => {
    return Object.entries(columnInfo)
      .filter(([col, info]) => requiredTypes.includes(info.type))
      .map(([col, info]) => col);
  };

  const getCurrentPlotType = () => {
    return plotTypes.find(p => p.value === plotType);
  };

  const canGeneratePlot = () => {
    const currentType = getCurrentPlotType();
    if (!currentType) return false;
    
    if (selectedColumns.length < currentType.minCols || selectedColumns.length > currentType.maxCols) {
      return false;
    }

    if (currentType.value === 'box' && selectedColumns.length === 2) {
      // For box plots with 2 columns, need one numeric and one categorical
      const col1Type = columnInfo[selectedColumns[0]]?.type;
      const col2Type = columnInfo[selectedColumns[1]]?.type;
      return (col1Type === 'numeric' && col2Type === 'categorical') ||
             (col1Type === 'categorical' && col2Type === 'numeric');
    }

    return selectedColumns.every(col => 
      currentType.types.includes(columnInfo[col]?.type)
    );
  };

  const generatePlot = async () => {
    if (!canGeneratePlot()) return;

    setIsGenerating(true);
    try {
      const plotConfig = {
        type: plotType,
        columns: selectedColumns,
        ...plotOptions
      };

      const response = await axios.post(`${API_BASE_URL}/plot`, plotConfig);
      
      if (response.data.plot) {
        setPlotData(JSON.parse(response.data.plot));
      }
    } catch (error) {
      onError(error.response?.data?.error || 'Failed to generate plot');
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePlotTypeChange = (newType) => {
    setPlotType(newType);
    setSelectedColumns([]);
    setPlotOptions({});
    setPlotData(null);
  };

  const handleColumnSelection = (column) => {
    const currentType = getCurrentPlotType();
    if (!currentType) return;

    if (selectedColumns.includes(column)) {
      setSelectedColumns(selectedColumns.filter(c => c !== column));
    } else if (selectedColumns.length < currentType.maxCols) {
      setSelectedColumns([...selectedColumns, column]);
    }
  };

  const getColumnChipColor = (column) => {
    const type = columnInfo[column]?.type;
    const colors = {
      'numeric': 'primary',
      'categorical': 'secondary',
      'text': 'default',
      'datetime': 'info',
      'boolean': 'warning'
    };
    return colors[type] || 'default';
  };

  const getPlotIcon = (type) => {
    const icons = {
      'violin': '🎻',
      'histogram': '📊',
      'box': '📦',
      'bar': '📈',
      'scatter': '🔵'
    };
    return icons[type] || '📊';
  };

  const currentType = getCurrentPlotType();
  const availableColumns = currentType ? getAvailableColumns(currentType.types) : [];

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h5">
          Plot Generator
        </Typography>
        {filterStatus.has_filters && (
          <Alert severity="info" sx={{ display: 'flex', alignItems: 'center' }}>
            <FilterList sx={{ mr: 1 }} />
            Filters active: {filterStatus.filtered_rows.toLocaleString()} / {filterStatus.total_rows.toLocaleString()} rows
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
                <InputLabel>Plot Type</InputLabel>
                <Select
                  value={plotType}
                  label="Plot Type"
                  onChange={(e) => handlePlotTypeChange(e.target.value)}
                >
                  {plotTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {getPlotIcon(type.value)} {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {currentType && (
                <Box sx={{ mb: 2 }}>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    {currentType.description}
                    <br />
                    Select {currentType.minCols === currentType.maxCols 
                      ? currentType.minCols 
                      : `${currentType.minCols}-${currentType.maxCols}`} 
                    column{(currentType.maxCols > 1) ? 's' : ''}.
                  </Alert>

                  <Typography variant="subtitle1" gutterBottom>
                    Available Columns ({currentType.types.join(', ')}):
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                    {availableColumns.map((column) => (
                      <Chip
                        key={column}
                        label={column}
                        color={getColumnChipColor(column)}
                        variant={selectedColumns.includes(column) ? 'filled' : 'outlined'}
                        onClick={() => handleColumnSelection(column)}
                        sx={{ cursor: 'pointer' }}
                      />
                    ))}
                  </Box>

                  {selectedColumns.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Selected Columns:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {selectedColumns.map((column) => (
                          <Chip
                            key={column}
                            label={column}
                            color={getColumnChipColor(column)}
                            onDelete={() => handleColumnSelection(column)}
                            size="small"
                          />
                        ))}
                      </Box>
                    </Box>
                  )}

                  {plotType === 'bar' && selectedColumns.length === 2 && (
                    <FormControlLabel
                      control={
                        <Switch
                          checked={plotOptions.stacked || false}
                          onChange={(e) => setPlotOptions({ ...plotOptions, stacked: e.target.checked })}
                        />
                      }
                      label="Stacked Bar Chart"
                    />
                  )}

                  <Button
                    fullWidth
                    variant="contained"
                    onClick={generatePlot}
                    disabled={!canGeneratePlot() || isGenerating}
                    startIcon={isGenerating ? <CircularProgress size={20} /> : <BarChart />}
                    sx={{ mt: 2 }}
                  >
                    {isGenerating ? 'Generating...' : 'Generate Plot'}
                  </Button>
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
              
              {plotData ? (
                <Plot
                  data={plotData.data}
                  layout={{
                    ...plotData.layout,
                    autosize: true,
                    margin: { t: 50, r: 50, b: 50, l: 50 }
                  }}
                  style={{ width: '100%', height: '500px' }}
                  useResizeHandler={true}
                />
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