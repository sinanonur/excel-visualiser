import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Slider,
  Grid,
  Button,
  Chip
} from '@mui/material';
import axios from 'axios';

const NumericFilter = ({ column, value, onChange, onError }) => {
  const [options, setOptions] = useState({});
  const [range, setRange] = useState([0, 100]);
  const [minValue, setMinValue] = useState('');
  const [maxValue, setMaxValue] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFilterOptions();
  }, [column]);

  useEffect(() => {
    if (value) {
      setMinValue(value.min?.toString() || '');
      setMaxValue(value.max?.toString() || '');
      if (options.min !== undefined && options.max !== undefined) {
        setRange([
          value.min !== undefined ? value.min : options.min,
          value.max !== undefined ? value.max : options.max
        ]);
      }
    }
  }, [value, options]);

  const loadFilterOptions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:5001/filter-options/${column}`);
      const opts = response.data;
      setOptions(opts);
      
      if (!value) {
        setRange([opts.min, opts.max]);
        setMinValue(opts.min.toString());
        setMaxValue(opts.max.toString());
      }
    } catch (error) {
      onError && onError('Failed to load filter options');
      console.error('Error loading filter options:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRangeChange = (event, newValue) => {
    setRange(newValue);
    setMinValue(newValue[0].toString());
    setMaxValue(newValue[1].toString());
    updateFilter(newValue[0], newValue[1]);
  };

  const handleMinChange = (event) => {
    const val = event.target.value;
    setMinValue(val);
    
    const numVal = parseFloat(val);
    if (!isNaN(numVal)) {
      const newMax = Math.max(numVal, range[1]);
      setRange([numVal, newMax]);
      updateFilter(numVal, newMax);
    }
  };

  const handleMaxChange = (event) => {
    const val = event.target.value;
    setMaxValue(val);
    
    const numVal = parseFloat(val);
    if (!isNaN(numVal)) {
      const newMin = Math.min(range[0], numVal);
      setRange([newMin, numVal]);
      updateFilter(newMin, numVal);
    }
  };

  const updateFilter = (min, max) => {
    if (options.min !== undefined && options.max !== undefined) {
      if (min <= options.min && max >= options.max) {
        // No filtering needed if range covers all data
        onChange(null);
      } else {
        onChange({
          type: 'numeric',
          min: min > options.min ? min : undefined,
          max: max < options.max ? max : undefined
        });
      }
    }
  };

  const resetFilter = () => {
    if (options.min !== undefined && options.max !== undefined) {
      setRange([options.min, options.max]);
      setMinValue(options.min.toString());
      setMaxValue(options.max.toString());
      onChange(null);
    }
  };

  if (loading) {
    return <Typography>Loading options...</Typography>;
  }

  const isFiltered = range[0] > options.min || range[1] < options.max;

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Filter by numeric range
      </Typography>

      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Chip
                size="small"
                label={`Min: ${options.min}`}
                variant="outlined"
              />
              <Chip
                size="small"
                label={`Max: ${options.max}`}
                variant="outlined"
              />
            </Box>
            <Slider
              value={range}
              onChange={handleRangeChange}
              min={options.min}
              max={options.max}
              step={(options.max - options.min) / 100}
              valueLabelDisplay="auto"
              sx={{ mb: 2 }}
            />
          </Grid>
          
          <Grid item xs={6}>
            <TextField
              label="Min Value"
              type="number"
              value={minValue}
              onChange={handleMinChange}
              fullWidth
              size="small"
              inputProps={{
                min: options.min,
                max: options.max,
                step: 'any'
              }}
            />
          </Grid>
          
          <Grid item xs={6}>
            <TextField
              label="Max Value"
              type="number"
              value={maxValue}
              onChange={handleMaxChange}
              fullWidth
              size="small"
              inputProps={{
                min: options.min,
                max: options.max,
                step: 'any'
              }}
            />
          </Grid>
        </Grid>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="body2" color="text.secondary">
            Mean: {options.mean?.toFixed(2)}, Std: {options.std?.toFixed(2)}
          </Typography>
        </Box>
        <Button
          size="small"
          onClick={resetFilter}
          disabled={!isFiltered}
        >
          Reset Range
        </Button>
      </Box>

      {isFiltered && (
        <Box sx={{ p: 1, backgroundColor: 'info.light', borderRadius: 1 }}>
          <Typography variant="body2">
            Filtering values from {range[0].toFixed(2)} to {range[1].toFixed(2)}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default NumericFilter;