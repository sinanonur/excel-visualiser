import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  Chip,
  Grid,
  Card,
  CardContent,
  Pagination,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress
} from '@mui/material';
import { Search } from '@mui/icons-material';
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

const getTypeColor = (type) => TYPE_COLORS[type] || 'default';
const getTypeIcon = (type) => TYPE_ICONS[type] || '❓';

const DataPreview = ({ data, columnInfo, refreshKey, onError }) => {
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [sort, setSort] = useState({ column: null, direction: 'asc' });
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [result, setResult] = useState({ data: [], total_pages: 1, total_rows: 0 });
  const [loading, setLoading] = useState(false);

  // Debounce typing so each keystroke does not hit the backend.
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // A sort column that no longer exists (new file or sheet) must be dropped.
  const sortColumn = sort.column && data.columns.includes(sort.column) ? sort.column : null;

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API_BASE_URL}/data-preview`, {
          params: {
            page,
            per_page: rowsPerPage,
            sort_by: sortColumn || undefined,
            sort_dir: sort.direction,
            search: search || undefined,
          },
        });
        if (!cancelled) {
          setResult(response.data);
          // The backend clamps out-of-range pages (e.g. after a filter shrinks the data).
          if (response.data.page !== page) setPage(response.data.page);
        }
      } catch (error) {
        if (!cancelled) {
          onError?.(error.response?.data?.error || 'Failed to load data preview');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [refreshKey, page, rowsPerPage, sortColumn, sort.direction, search, onError]);

  const handleSort = (column) => {
    setSort((previous) => {
      if (previous.column !== column) return { column, direction: 'asc' };
      if (previous.direction === 'asc') return { column, direction: 'desc' };
      return { column: null, direction: 'asc' };
    });
    setPage(1);
  };

  const renderCell = (value) => {
    if (value === null || value === undefined) {
      return <span style={{ color: '#999', fontStyle: 'italic' }}>null</span>;
    }
    return String(value);
  };

  const totalRows = data.total_rows ?? data.shape[0];
  const rowSummary = data.has_filters
    ? `${data.filtered_rows.toLocaleString()} of ${totalRows.toLocaleString()}`
    : totalRows.toLocaleString();

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Data Overview
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                {data.has_filters ? 'Rows (filtered)' : 'Total Rows'}
              </Typography>
              <Typography variant="h4" data-testid="row-summary">
                {rowSummary}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Columns
              </Typography>
              <Typography variant="h4">
                {data.columns.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Columns with Lists
              </Typography>
              <Typography variant="h4">
                {Object.values(columnInfo).filter(info => info.has_lists).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Data Types
              </Typography>
              <Typography variant="h4">
                {new Set(Object.values(columnInfo).map(info => info.type)).size}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Data Preview
        </Typography>
        <TextField
          size="small"
          placeholder="Search all columns..."
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          inputProps={{ 'aria-label': 'Search all columns' }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search fontSize="small" />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 260 }}
        />
        <FormControl size="small" sx={{ minWidth: 110 }}>
          <InputLabel id="rows-per-page-label">Rows</InputLabel>
          <Select
            labelId="rows-per-page-label"
            label="Rows"
            value={rowsPerPage}
            onChange={(event) => {
              setRowsPerPage(event.target.value);
              setPage(1);
            }}
          >
            {[25, 50, 100].map((size) => (
              <MenuItem key={size} value={size}>{size} / page</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {search && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }} data-testid="search-summary">
          {result.total_rows.toLocaleString()} rows match "{search}"
        </Typography>
      )}

      <Box sx={{ height: 4 }}>{loading && <LinearProgress />}</Box>

      <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              {data.columns.map((column) => (
                <TableCell
                  key={column}
                  sx={{ fontWeight: 'bold', minWidth: 120 }}
                  sortDirection={sortColumn === column ? sort.direction : false}
                >
                  <Box>
                    <TableSortLabel
                      active={sortColumn === column}
                      direction={sortColumn === column ? sort.direction : 'asc'}
                      onClick={() => handleSort(column)}
                    >
                      <Typography variant="subtitle2">
                        {column}
                      </Typography>
                    </TableSortLabel>
                    <Box>
                      <Chip
                        size="small"
                        label={`${getTypeIcon(columnInfo[column]?.type)} ${columnInfo[column]?.type}`}
                        color={getTypeColor(columnInfo[column]?.type)}
                        sx={{ mt: 0.5 }}
                      />
                      {columnInfo[column]?.has_lists && (
                        <Chip
                          size="small"
                          label="📋 Lists"
                          color="warning"
                          sx={{ mt: 0.5, ml: 0.5 }}
                        />
                      )}
                    </Box>
                  </Box>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {result.data.map((row, index) => (
              <TableRow key={index} hover>
                {data.columns.map((column) => (
                  <TableCell key={column} sx={{ maxWidth: 320 }}>
                    <Typography
                      variant="body2"
                      noWrap
                      title={row[column] === null || row[column] === undefined ? '' : String(row[column])}
                    >
                      {renderCell(row[column])}
                    </Typography>
                  </TableCell>
                ))}
              </TableRow>
            ))}
            {result.data.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={Math.max(data.columns.length, 1)} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                    {search ? 'No rows match the search' : 'No rows to show'}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
        <Pagination
          count={result.total_pages || 1}
          page={page}
          onChange={(event, newPage) => setPage(newPage)}
          color="primary"
          size="large"
        />
      </Box>
    </Box>
  );
};

export default DataPreview;
