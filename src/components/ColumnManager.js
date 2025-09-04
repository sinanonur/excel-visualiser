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
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert
} from '@mui/material';
import { ExpandMore, List, Settings } from '@mui/icons-material';
import axios from 'axios';
import API_BASE_URL from '../config';

const ColumnManager = ({ data, columnInfo, onColumnInfoUpdate, onError }) => {
  const [expandDialog, setExpandDialog] = useState({ open: false, column: null });
  const [isExpanding, setIsExpanding] = useState(false);

  const handleTypeChange = async (column, newType) => {
    try {
      await axios.post(`${API_BASE_URL}/update-column-type`, {
        column: column,
        type: newType
      });
      
      const updatedInfo = { ...columnInfo };
      updatedInfo[column].type = newType;
      onColumnInfoUpdate(updatedInfo);
    } catch (error) {
      onError('Failed to update column type');
    }
  };

  const handleExpandColumn = async (column) => {
    setIsExpanding(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/expand-column`, {
        column: column
      });
      
      if (response.data.success) {
        onColumnInfoUpdate(response.data.column_info);
        setExpandDialog({ open: false, column: null });
        
        // Refresh the page to show new columns
        window.location.reload();
      }
    } catch (error) {
      onError(error.response?.data?.error || 'Failed to expand column');
    } finally {
      setIsExpanding(false);
    }
  };

  const getTypeColor = (type) => {
    const colors = {
      'numeric': 'primary',
      'categorical': 'secondary',
      'text': 'default',
      'datetime': 'info',
      'boolean': 'warning',
      'empty': 'error'
    };
    return colors[type] || 'default';
  };

  const getTypeIcon = (type) => {
    const icons = {
      'numeric': '🔢',
      'categorical': '🏷️',
      'text': '📝',
      'datetime': '📅',
      'boolean': '✅',
      'empty': '❌'
    };
    return icons[type] || '❓';
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Column Management
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage column data types and expand columns containing lists or sets into separate columns.
      </Typography>

      <Grid container spacing={2}>
        {Object.entries(columnInfo).map(([colName, info]) => (
          <Grid item xs={12} sm={6} md={4} key={colName}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom noWrap>
                  {colName}
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Chip
                    icon={<span>{getTypeIcon(info.type)}</span>}
                    label={info.type}
                    color={getTypeColor(info.type)}
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  {info.has_lists && (
                    <Chip
                      icon={<List />}
                      label="Contains Lists"
                      color="warning"
                      size="small"
                    />
                  )}
                </Box>

                <Typography variant="body2" color="text.secondary">
                  Unique values: {info.unique_values}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Null values: {info.null_count}
                </Typography>

                <FormControl fullWidth sx={{ mt: 2 }}>
                  <InputLabel>Data Type</InputLabel>
                  <Select
                    value={info.type}
                    label="Data Type"
                    onChange={(e) => handleTypeChange(colName, e.target.value)}
                    size="small"
                  >
                    <MenuItem value="numeric">🔢 Numeric</MenuItem>
                    <MenuItem value="categorical">🏷️ Categorical</MenuItem>
                    <MenuItem value="text">📝 Text</MenuItem>
                    <MenuItem value="datetime">📅 DateTime</MenuItem>
                    <MenuItem value="boolean">✅ Boolean</MenuItem>
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
        onClose={() => setExpandDialog({ open: false, column: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Expand Column: {expandDialog.column}
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            This will create new columns for each item in the lists/sets found in this column.
            For example, if a cell contains "[apple, banana, cherry]", it will create separate
            columns for each fruit.
          </Alert>
          <Typography variant="body2" color="text.secondary">
            Column: <strong>{expandDialog.column}</strong>
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This operation will add new columns to your dataset and may take a moment to process.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setExpandDialog({ open: false, column: null })}
            disabled={isExpanding}
          >
            Cancel
          </Button>
          <Button
            onClick={() => handleExpandColumn(expandDialog.column)}
            variant="contained"
            disabled={isExpanding}
            startIcon={isExpanding ? <Settings className="rotating" /> : <ExpandMore />}
          >
            {isExpanding ? 'Expanding...' : 'Expand Column'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ColumnManager;