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
import useFilterOptions from './useFilterOptions';

const NumericFilter = ({ column, value, onChange, onError }) => {
  const { options, loading } = useFilterOptions(column, onError);
  const [range, setRange] = useState([0, 100]);
  const [pendingRange, setPendingRange] = useState([0, 100]);
  const [isDirty, setIsDirty] = useState(false);

  const valueMin = value?.min;
  const valueMax = value?.max;
  useEffect(() => {
    if (typeof options.min === 'number' && typeof options.max === 'number') {
      const initialRange = [valueMin ?? options.min, valueMax ?? options.max];
      setRange(initialRange);
      setPendingRange(initialRange);
      setIsDirty(false);
    }
  }, [valueMin, valueMax, options.min, options.max]);

  const handleSliderChange = (event, newValue) => {
    setPendingRange(newValue);
    setIsDirty(true);
  };

  const handleMinInputChange = (event) => {
    const newMin = event.target.value === '' ? options.min : parseFloat(event.target.value);
    if (!isNaN(newMin) && newMin <= pendingRange[1]) {
      setPendingRange([newMin, pendingRange[1]]);
      setIsDirty(true);
    }
  };

  const handleMaxInputChange = (event) => {
    const newMax = event.target.value === '' ? options.max : parseFloat(event.target.value);
    if (!isNaN(newMax) && newMax >= pendingRange[0]) {
      setPendingRange([pendingRange[0], newMax]);
      setIsDirty(true);
    }
  };

  const handleApply = () => {
    setRange(pendingRange);

    const [min, max] = pendingRange;
    if (min <= options.min && max >= options.max) {
      onChange(null);
    } else {
      onChange({
        type: 'numeric',
        min: min > options.min ? min : undefined,
        max: max < options.max ? max : undefined,
      });
    }
    setIsDirty(false);
  };

  const resetFilter = () => {
    const fullRange = [options.min, options.max];
    setPendingRange(fullRange);
    setRange(fullRange);
    onChange(null);
    setIsDirty(false);
  };

  if (loading) {
    return <Typography>Loading options...</Typography>;
  }

  if (typeof options.min !== 'number' || typeof options.max !== 'number') {
    return <Typography color="text.secondary">This column has no numeric values to filter.</Typography>;
  }

  const isFiltered = range[0] > options.min || range[1] < options.max;

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Filter by numeric range
      </Typography>

      <Box sx={{ mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Chip size="small" label={`Min: ${options.min}`} variant="outlined" />
              <Chip size="small" label={`Max: ${options.max}`} variant="outlined" />
            </Box>
            <Slider
              value={pendingRange}
              onChange={handleSliderChange}
              min={options.min}
              max={options.max}
              step={(options.max - options.min) / 100 || 1}
              disabled={options.min === options.max}
              valueLabelDisplay="auto"
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              label="Min Value"
              type="number"
              value={pendingRange[0]}
              onChange={handleMinInputChange}
              fullWidth
              size="small"
              inputProps={{ min: options.min, max: options.max, step: 'any' }}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              label="Max Value"
              type="number"
              value={pendingRange[1]}
              onChange={handleMaxInputChange}
              fullWidth
              size="small"
              inputProps={{ min: options.min, max: options.max, step: 'any' }}
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
        <Box>
          <Button size="small" onClick={resetFilter} disabled={!isFiltered && !isDirty}>
            Reset
          </Button>
          <Button
            size="small"
            variant="contained"
            onClick={handleApply}
            disabled={!isDirty}
            sx={{ ml: 1 }}
          >
            Apply
          </Button>
        </Box>
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