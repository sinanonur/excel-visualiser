import React, { useState, useEffect } from 'react';
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
import axios from 'axios';
import API_BASE_URL from '../../config';

const CategoricalFilter = ({ column, value, onChange, onError }) => {
  const [options, setOptions] = useState([]);
  const [selectedValues, setSelectedValues] = useState(value?.values || []);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFilterOptions();
  }, [column]);

  useEffect(() => {
    // Update parent when selection changes
    if (selectedValues.length > 0) {
      onChange({
        type: 'categorical',
        values: selectedValues
      });
    } else {
      onChange(null);
    }
  }, [selectedValues, onChange]);

  const loadFilterOptions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/filter-options/${column}`);
      setOptions(response.data.values || []);
    } catch (error) {
      onError && onError('Failed to load filter options');
      console.error('Error loading filter options:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleValueChange = (optionValue, checked) => {
    if (checked) {
      setSelectedValues(prev => [...prev, optionValue]);
    } else {
      setSelectedValues(prev => prev.filter(v => v !== optionValue));
    }
  };

  const selectAll = () => {
    setSelectedValues([...filteredOptions]);
  };

  const selectNone = () => {
    setSelectedValues([]);
  };

  const filteredOptions = options.filter(option =>
    option.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <Typography>Loading options...</Typography>;
  }

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Select categories to include ({selectedValues.length} of {options.length} selected)
      </Typography>

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
          disabled={filteredOptions.length === selectedValues.length}
        >
          Select All
        </Button>
        <Button
          size="small"
          onClick={selectNone}
          disabled={selectedValues.length === 0}
        >
          Select None
        </Button>
      </Box>

      <Divider sx={{ mb: 2 }} />

      <FormGroup sx={{ maxHeight: 300, overflowY: 'auto' }}>
        {filteredOptions.map((option) => (
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

      {filteredOptions.length === 0 && searchTerm && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
          No categories found matching "{searchTerm}"
        </Typography>
      )}
    </Box>
  );
};

export default CategoricalFilter;