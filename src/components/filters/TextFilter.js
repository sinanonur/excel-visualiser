import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  FormControlLabel,
  Switch,
  RadioGroup,
  Radio,
  FormControl,
  FormLabel,
  Button,
  Chip,
  Alert
} from '@mui/material';
import axios from 'axios';

const TextFilter = ({ column, value, onChange, onError }) => {
  const [options, setOptions] = useState({});
  const [searchValue, setSearchValue] = useState(value?.value || '');
  const [searchType, setSearchType] = useState(value?.search_type || 'contains');
  const [caseSensitive, setCaseSensitive] = useState(value?.case_sensitive || false);
  const [loading, setLoading] = useState(true);
  const [regexError, setRegexError] = useState('');

  useEffect(() => {
    loadFilterOptions();
  }, [column]);

  useEffect(() => {
    updateFilter();
  }, [searchValue, searchType, caseSensitive]);

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

  const updateFilter = () => {
    setRegexError('');
    
    if (!searchValue.trim()) {
      onChange(null);
      return;
    }

    // Validate regex if using regex search
    if (searchType === 'regex') {
      try {
        new RegExp(searchValue);
      } catch (error) {
        setRegexError('Invalid regular expression');
        return;
      }
    }

    onChange({
      type: 'text',
      search_type: searchType,
      value: searchValue,
      case_sensitive: caseSensitive
    });
  };

  const clearFilter = () => {
    setSearchValue('');
    setRegexError('');
    onChange(null);
  };

  const handleSampleClick = (sampleValue) => {
    setSearchValue(sampleValue);
  };

  if (loading) {
    return <Typography>Loading options...</Typography>;
  }

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Filter by text content
      </Typography>

      <FormControl component="fieldset" sx={{ mb: 2 }}>
        <FormLabel component="legend">Search Type</FormLabel>
        <RadioGroup
          row
          value={searchType}
          onChange={(e) => setSearchType(e.target.value)}
        >
          <FormControlLabel
            value="contains"
            control={<Radio size="small" />}
            label="Contains"
          />
          <FormControlLabel
            value="regex"
            control={<Radio size="small" />}
            label="Regular Expression"
          />
        </RadioGroup>
      </FormControl>

      <TextField
        fullWidth
        label={searchType === 'regex' ? 'Regular Expression' : 'Search Text'}
        value={searchValue}
        onChange={(e) => setSearchValue(e.target.value)}
        placeholder={
          searchType === 'regex' 
            ? 'e.g., ^[A-Z].*ing$' 
            : 'e.g., New York'
        }
        error={!!regexError}
        helperText={
          regexError || 
          (searchType === 'regex' 
            ? 'Use regex patterns like ^start, end$, [A-Z], \\d+' 
            : 'Search for text within values'
          )
        }
        sx={{ mb: 2 }}
      />

      <FormControlLabel
        control={
          <Switch
            checked={caseSensitive}
            onChange={(e) => setCaseSensitive(e.target.checked)}
            size="small"
          />
        }
        label="Case sensitive"
        sx={{ mb: 2 }}
      />

      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        <Button
          size="small"
          onClick={clearFilter}
          disabled={!searchValue}
        >
          Clear Filter
        </Button>
      </Box>

      {searchType === 'regex' && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>Regex Examples:</strong><br />
            • <code>^New</code> - Starts with "New"<br />
            • <code>York$</code> - Ends with "York"<br />
            • <code>[0-9]+</code> - Contains numbers<br />
            • <code>^[A-Z][a-z]+</code> - Starts with capital letter
          </Typography>
        </Alert>
      )}

      {options.sample_values && options.sample_values.length > 0 && (
        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Sample values (click to use):
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {options.sample_values.map((sample, index) => (
              <Chip
                key={index}
                size="small"
                label={sample}
                onClick={() => handleSampleClick(sample)}
                clickable
                variant="outlined"
                sx={{ maxWidth: 200 }}
              />
            ))}
          </Box>
        </Box>
      )}

      {searchValue && !regexError && (
        <Box sx={{ mt: 2, p: 1, backgroundColor: 'info.light', borderRadius: 1 }}>
          <Typography variant="body2">
            {searchType === 'regex' ? 'Regex' : 'Text'} filter: 
            <code style={{ marginLeft: 4 }}>
              {searchValue}
            </code>
            {caseSensitive && ' (case sensitive)'}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default TextFilter;