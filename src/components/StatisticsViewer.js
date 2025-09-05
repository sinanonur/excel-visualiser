import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
  Alert,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import axios from 'axios';
import API_BASE_URL from '../config';

const StatisticsViewer = ({ columnInfo, onError }) => {
  const [selectedColumn, setSelectedColumn] = useState('');
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const availableColumns = Object.keys(columnInfo);

  useEffect(() => {
    if (selectedColumn) {
      fetchStatistics();
    }
  }, [selectedColumn]);

  const fetchStatistics = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/statistics/${selectedColumn}`);
      setStats(response.data);
    } catch (error) {
      onError(error.response?.data?.error || `Failed to fetch statistics for ${selectedColumn}`);
      setStats(null);
    } finally {
      setIsLoading(false);
    }
  };

  const renderNumericStats = () => {
    if (!stats) return null;
    const generalStats = {
      'Count': stats.count,
      'Mean': stats.mean?.toFixed(4),
      'Std Dev': stats.std?.toFixed(4),
      'Min': stats.min,
      '25% (Q1)': stats['25%'],
      '50% (Median)': stats['50%'],
      '75% (Q3)': stats['75%'],
      'Max': stats.max
    };

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom>General Statistics</Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableBody>
                {Object.entries(generalStats).map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell component="th" scope="row">{key}</TableCell>
                    <TableCell align="right">{value}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom>Outliers</Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Found {stats.num_outliers} outlier(s). Showing up to 5.
          </Typography>
          {stats.outliers && stats.outliers.length > 0 ? (
            <List dense component={Paper}>
              {stats.outliers.map((outlier, index) => (
                <ListItem key={index}>
                  <ListItemText primary={outlier} />
                </ListItem>
              ))}
            </List>
          ) : (
            <Alert severity="info">No outliers detected.</Alert>
          )}
        </Grid>
      </Grid>
    );
  };

  const renderCategoricalStats = () => {
    if (!stats || !stats.value_counts) return null;
    return (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>Value Distribution</Typography>
           <Typography variant="body2" color="text.secondary" gutterBottom>
            Showing top 20 unique values out of {stats.num_unique}.
          </Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableBody>
                {Object.entries(stats.value_counts).map(([value, count]) => (
                  <TableRow key={value}>
                    <TableCell>{value}</TableCell>
                    <TableCell align="right">{count}</TableCell>
                    <TableCell align="right">{stats.percentages[value].toFixed(2)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
      </Grid>
    );
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Column Statistics
      </Typography>
      <FormControl fullWidth sx={{ mb: 3 }}>
        <InputLabel>Select a Column</InputLabel>
        <Select
          value={selectedColumn}
          label="Select a Column"
          onChange={(e) => setSelectedColumn(e.target.value)}
        >
          {availableColumns.map((col) => (
            <MenuItem key={col} value={col}>
              {col}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {isLoading && <CircularProgress />}

      {!isLoading && stats && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Statistics for: {stats.column} ({stats.type})
            </Typography>

            {stats.type === 'numeric' && renderNumericStats()}
            {stats.type === 'categorical' && renderCategoricalStats()}
            {stats.type === 'text' && <Alert severity="info">Basic stats available for text columns: {stats.num_unique} unique values.</Alert>}
            {stats.type === 'boolean' && renderCategoricalStats()}

          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default StatisticsViewer;
