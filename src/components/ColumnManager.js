import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Select,
  MenuItem,
  FormControl,
  FormControlLabel,
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Radio,
  RadioGroup,
  TextField,
  Alert
} from '@mui/material';
import { ExpandMore, List } from '@mui/icons-material';
import axios from 'axios';
import API_BASE_URL from '../config';

const TYPE_COLORS = {
  'numeric': 'primary',
  'categorical': 'secondary',
  'text': 'default',
  'datetime': 'info',
  'boolean': 'warning',
  'empty': 'error'
};

const TYPE_ICONS = {
  'numeric': '🔢',
  'categorical': '🏷️',
  'text': '📝',
  'datetime': '📅',
  'boolean': '✅',
  'empty': '❌'
};

const ColumnManager = ({ columnInfo, onDatasetUpdate, onNotice, onError }) => {
  const [expandDialog, setExpandDialog] = useState({ open: false, column: null });
  const [expandMode, setExpandMode] = useState('onehot');
  const [isExpanding, setIsExpanding] = useState(false);
  const [pendingColumn, setPendingColumn] = useState(null);
  const [search, setSearch] = useState('');

  const handleTypeChange = async (column, newType) => {
    setPendingColumn(column);
    try {
      // The backend converts the values, not just the label, so it can fail.
      const response = await axios.post(`${API_BASE_URL}/update-column-type`, {
        column: column,
        type: newType
      });
      onDatasetUpdate(response.data);
      const notes = [];
      if (response.data.failed_values > 0) {
        notes.push(`${response.data.failed_values.toLocaleString()} values could not be converted and are now missing`);
      }
      if (response.data.filter_removed) {
        notes.push('the filter on this column was removed');
      }
      if (notes.length > 0) {
        onNotice?.('warning', `"${column}" is now ${newType}: ${notes.join('; ')}.`);
      }
    } catch (error) {
      onError(error.response?.data?.error || 'Failed to update column type');
    } finally {
      setPendingColumn(null);
    }
  };

  const closeDialog = () => setExpandDialog({ open: false, column: null });

  const handleExpandColumn = async (column) => {
    setIsExpanding(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/expand-column`, {
        column: column,
        mode: expandMode
      });

      if (response.data.success) {
        onDatasetUpdate(response.data);
        onNotice?.('success', `Added ${response.data.new_columns.length} columns from "${column}"`);
        closeDialog();
      }
    } catch (error) {
      onError(error.response?.data?.error || 'Failed to expand column');
    } finally {
      setIsExpanding(false);
    }
  };

  const entries = Object.entries(columnInfo).filter(([colName]) =>
    colName.toLowerCase().includes(search.trim().toLowerCase())
  );

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Column Management
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Change a column's data type (its values are converted) and expand columns containing lists or sets into separate columns.
      </Typography>

      {Object.keys(columnInfo).length > 12 && (
        <TextField
          size="small"
          placeholder="Search columns..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          sx={{ mb: 2, minWidth: 260 }}
        />
      )}

      <Grid container spacing={2}>
        {entries.map(([colName, info]) => (
          <Grid item xs={12} sm={6} md={4} key={colName}>
            <Card variant="outlined" data-testid={`column-card-${colName}`}>
              <CardContent>
                <Typography variant="h6" gutterBottom noWrap title={colName}>
                  {colName}
                </Typography>

                <Box sx={{ mb: 2 }}>
                  <Chip
                    icon={<span>{TYPE_ICONS[info.type] || '❓'}</span>}
                    label={info.type}
                    color={TYPE_COLORS[info.type] || 'default'}
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  {info.has_lists && (
                    <Chip
                      icon={<List />}
                      label="Contains Lists"
                      color="warning"
                      size="small"
                      sx={{ mr: 1 }}
                    />
                  )}
                  {info.user_set && (
                    <Chip label="Set manually" size="small" variant="outlined" />
                  )}
                </Box>

                <Typography variant="body2" color="text.secondary">
                  Unique values: {info.unique_values?.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Null values: {info.null_count?.toLocaleString()}
                </Typography>

                <FormControl fullWidth sx={{ mt: 2 }} disabled={pendingColumn === colName}>
                  <InputLabel>Data Type</InputLabel>
                  <Select
                    value={info.type}
                    label="Data Type"
                    onChange={(e) => handleTypeChange(colName, e.target.value)}
                    size="small"
                    inputProps={{ 'aria-label': `Data type for ${colName}` }}
                  >
                    <MenuItem value="numeric">🔢 Numeric</MenuItem>
                    <MenuItem value="categorical">🏷️ Categorical</MenuItem>
                    <MenuItem value="text">📝 Text</MenuItem>
                    <MenuItem value="datetime">📅 DateTime</MenuItem>
                    <MenuItem value="boolean">✅ Boolean</MenuItem>
                    {info.type === 'empty' && (
                      <MenuItem value="empty" disabled>❌ Empty</MenuItem>
                    )}
                  </Select>
                </FormControl>
              </CardContent>

              {info.has_lists && (
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<ExpandMore />}
                    onClick={() => setExpandDialog({ open: true, column: colName })}
                    color="primary"
                  >
                    Expand Lists
                  </Button>
                </CardActions>
              )}
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog
        open={expandDialog.open}
        onClose={isExpanding ? undefined : closeDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Expand Column: {expandDialog.column}
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Cells like "[apple, banana]" or "{'{'}new, senior{'}'}" are split into items and added as new columns.
            The original column is kept.
          </Alert>
          <RadioGroup value={expandMode} onChange={(event) => setExpandMode(event.target.value)}>
            <FormControlLabel
              value="onehot"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body1">One true/false column per item</Typography>
                  <Typography variant="body2" color="text.secondary">
                    e.g. "{expandDialog.column} [apple]". Best for filtering and counting. Limited to the 50 most frequent items.
                  </Typography>
                </Box>
              }
              sx={{ alignItems: 'flex-start', mb: 1 }}
            />
            <FormControlLabel
              value="positional"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body1">One column per position</Typography>
                  <Typography variant="body2" color="text.secondary">
                    e.g. "{expandDialog.column}_item_1", "{expandDialog.column}_item_2". Best when the order of items matters.
                  </Typography>
                </Box>
              }
              sx={{ alignItems: 'flex-start' }}
            />
          </RadioGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog} disabled={isExpanding}>
            Cancel
          </Button>
          <Button
            onClick={() => handleExpandColumn(expandDialog.column)}
            variant="contained"
            disabled={isExpanding}
            startIcon={<ExpandMore />}
          >
            {isExpanding ? 'Expanding...' : 'Expand Column'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ColumnManager;
