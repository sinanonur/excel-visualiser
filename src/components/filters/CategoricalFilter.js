import React, { useState } from 'react';
import {
  Box,
  Typography,
  FormControlLabel,
  Checkbox,
  Button,
  FormGroup,
  TextField,
  InputAdornment,
  Divider
} from '@mui/material';
import { Search } from '@mui/icons-material';
import useFilterOptions from './useFilterOptions';

// Controlled by `value` ({ type: 'categorical', values: [...] } or undefined).
const CategoricalFilter = ({ column, value, onChange, onError }) => {
  const { options: response, loading } = useFilterOptions(column, onError);
  const [searchTerm, setSearchTerm] = useState('');

  const options = response.values || [];
  const selectedValues = value?.values || [];

  const emit = (values) => {
    onChange(values.length > 0 ? { type: 'categorical', values } : null);
  };

  const handleValueChange = (optionValue, checked) => {
    emit(checked
      ? [...selectedValues, optionValue]
      : selectedValues.filter(v => v !== optionValue));
  };

  const filteredOptions = options.filter(option =>
    option.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // "Select All" adds the visible (searched) options to the current selection.
  const selectAll = () => emit(Array.from(new Set([...selectedValues, ...filteredOptions])));
  const allVisibleSelected = filteredOptions.every(option => selectedValues.includes(option));

  if (loading) {
    return <Typography>Loading options...</Typography>;
  }

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Select categories to include ({selectedValues.length} of {options.length} selected)
      </Typography>

      {response.truncated && (
        <Typography variant="caption" color="warning.main" component="div" sx={{ mb: 1 }}>
          Showing the first {options.length.toLocaleString()} of {response.total_values.toLocaleString()} categories.
          Use a text filter for the rest.
        </Typography>
      )}

      <TextField
        fullWidth
        size="small"
        placeholder="Search categories..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 2 }}
      />

      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        <Button
          size="small"
          onClick={selectAll}
          disabled={filteredOptions.length === 0 || allVisibleSelected}
        >
          Select All
        </Button>
        <Button
          size="small"
          onClick={() => emit([])}
          disabled={selectedValues.length === 0}
        >
          Select None
        </Button>
      </Box>

      <Divider sx={{ mb: 2 }} />

      <FormGroup sx={{ maxHeight: 300, overflowY: 'auto', flexWrap: 'nowrap' }}>
        {filteredOptions.slice(0, 500).map((option) => (
          <FormControlLabel
            key={option}
            control={
              <Checkbox
                checked={selectedValues.includes(option)}
                onChange={(e) => handleValueChange(option, e.target.checked)}
                size="small"
              />
            }
            label={option}
          />
        ))}
      </FormGroup>

      {filteredOptions.length > 500 && (
        <Typography variant="caption" color="text.secondary">
          {(filteredOptions.length - 500).toLocaleString()} more categories hidden. Search to narrow the list.
        </Typography>
      )}

      {filteredOptions.length === 0 && searchTerm && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
          No categories found matching "{searchTerm}"
        </Typography>
      )}
    </Box>
  );
};

export default CategoricalFilter;
