import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, TextField, Grid, Button, Chip } from '@mui/material';
import axios from 'axios';
import API_BASE_URL from '../../config';

const DateFilter = ({ column, value, onChange, onError }) => {
  const [options, setOptions] = useState({ min: null, max: null });
  const [loading, setLoading] = useState(true);
  const [start, setStart] = useState(value?.start || '');
  const [end, setEnd] = useState(value?.end || '');

  // Keep the latest onError without retriggering the loader on parent re-renders
  const onErrorRef = useRef(onError);
  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    let cancelled = false;
    const loadFilterOptions = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/filter-options`, { params: { column } });
        if (!cancelled) {
          setOptions({ min: response.data?.min ?? null, max: response.data?.max ?? null });
        }
      } catch (error) {
        if (!cancelled) {
          onErrorRef.current?.('Failed to load filter options');
        }
        console.error('Error loading filter options:', error);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    loadFilterOptions();
    return () => {
      cancelled = true;
    };
  }, [column]);

  // Sync inputs when the stored filter config changes (or column switches)
  const valueStart = value?.start || '';
  const valueEnd = value?.end || '';
  useEffect(() => {
    setStart(valueStart);
    setEnd(valueEnd);
  }, [valueStart, valueEnd, column]);

  const invalidRange = Boolean(start && end && start > end);

  const emit = (nextStart, nextEnd) => {
    if (nextStart && nextEnd && nextStart > nextEnd) {
      return;
    }
    if (!nextStart && !nextEnd) {
      onChange(null);
    } else {
      onChange({
        type: 'datetime',
        start: nextStart || undefined,
        end: nextEnd || undefined,
      });
    }
  };

  const handleStartChange = (event) => {
    const next = event.target.value;
    setStart(next);
    emit(next, end);
  };

  const handleEndChange = (event) => {
    const next = event.target.value;
    setEnd(next);
    emit(start, next);
  };

  const handleClear = () => {
    setStart('');
    setEnd('');
    onChange(null);
  };

  if (loading) {
    return <Typography>Loading options...</Typography>;
  }

  const inputProps = {
    min: options.min || undefined,
    max: options.max || undefined,
  };

  let summary = 'No date filter applied';
  if (!invalidRange) {
    if (start && end) summary = `Showing dates from ${start} to ${end}`;
    else if (start) summary = `Showing dates on or after ${start}`;
    else if (end) summary = `Showing dates on or before ${end}`;
  }

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Filter by date range
      </Typography>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Chip size="small" variant="outlined" label={`Earliest: ${options.min ?? '–'}`} />
        <Chip size="small" variant="outlined" label={`Latest: ${options.max ?? '–'}`} />
      </Box>

      <Grid container spacing={2} alignItems="flex-start" sx={{ mb: 2 }}>
        <Grid item xs={6}>
          <TextField
            label="From"
            type="date"
            value={start}
            onChange={handleStartChange}
            fullWidth
            size="small"
            InputLabelProps={{ shrink: true }}
            inputProps={inputProps}
            error={invalidRange}
          />
        </Grid>
        <Grid item xs={6}>
          <TextField
            label="To"
            type="date"
            value={end}
            onChange={handleEndChange}
            fullWidth
            size="small"
            InputLabelProps={{ shrink: true }}
            inputProps={inputProps}
            error={invalidRange}
            helperText={invalidRange ? 'End date must not be before start date' : undefined}
          />
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {summary}
        </Typography>
        <Button size="small" onClick={handleClear} disabled={!start && !end}>
          Clear
        </Button>
      </Box>
    </Box>
  );
};

export default DateFilter;
