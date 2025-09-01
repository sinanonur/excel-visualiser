import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  FormControlLabel,
  Radio,
  RadioGroup,
  FormControl,
  Button
} from '@mui/material';
import axios from 'axios';

const BooleanFilter = ({ column, value, onChange, onError }) => {
  const [options, setOptions] = useState({});
  const [selectedValue, setSelectedValue] = useState(value?.value !== undefined ? value.value.toString() : '');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFilterOptions();
  }, [column]);

  useEffect(() => {
    if (selectedValue === '') {
      onChange(null);
    } else {
      onChange({
        type: 'boolean',
        value: selectedValue === 'true'
      });
    }
  }, [selectedValue, onChange]);

  const loadFilterOptions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:5001/filter-options/${column}`);
      setOptions(response.data);
    } catch (error) {
      onError && onError('Failed to load filter options');
      console.error('Error loading filter options:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearFilter = () => {
    setSelectedValue('');
  };

  if (loading) {
    return <Typography>Loading options...</Typography>;
  }

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Filter by boolean value
      </Typography>

      <FormControl component="fieldset">
        <RadioGroup
          value={selectedValue}
          onChange={(e) => setSelectedValue(e.target.value)}
        >
          <FormControlLabel
            value=""
            control={<Radio size="small" />}
            label="Show all values"
          />
          {options.values && options.values.map((boolVal) => (
            <FormControlLabel
              key={boolVal.toString()}
              value={boolVal.toString()}
              control={<Radio size="small" />}
              label={boolVal ? 'True' : 'False'}
            />
          ))}
        </RadioGroup>
      </FormControl>

      <Box sx={{ mt: 2 }}>
        <Button
          size="small"
          onClick={clearFilter}
          disabled={selectedValue === ''}
        >
          Clear Filter
        </Button>
      </Box>

      {selectedValue !== '' && (
        <Box sx={{ mt: 2, p: 1, backgroundColor: 'info.light', borderRadius: 1 }}>
          <Typography variant="body2">
            Showing only: {selectedValue === 'true' ? 'True' : 'False'} values
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default BooleanFilter;