import React from 'react';
import {
  Box,
  Typography,
  FormControlLabel,
  Radio,
  RadioGroup,
  FormControl,
  Button
} from '@mui/material';
import useFilterOptions from './useFilterOptions';

// Controlled by `value` ({ type: 'boolean', value: true|false } or undefined).
const BooleanFilter = ({ column, value, onChange, onError }) => {
  const { options, loading } = useFilterOptions(column, onError);
  const selectedValue = value?.value === undefined || value?.value === null ? '' : String(value.value);

  const handleChange = (newValue) => {
    onChange(newValue === '' ? null : { type: 'boolean', value: newValue === 'true' });
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
          onChange={(e) => handleChange(e.target.value)}
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
          onClick={() => handleChange('')}
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
