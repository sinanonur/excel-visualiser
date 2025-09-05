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
  Paper,
  Chip,
  Grid,
  Card,
  CardContent,
  Pagination
} from '@mui/material';
import axios from 'axios';
import API_BASE_URL from '../config';

const DataPreview = ({ data, columnInfo }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageData, setPageData] = useState([]);
  const [totalPages, setTotalPages] = useState(1);
  const rowsPerPage = 25;

  useEffect(() => {
    loadPageData(1);
  }, [data]);

  const loadPageData = async (page) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/data-preview?page=${page}&per_page=${rowsPerPage}`);
      setPageData(response.data.data);
      setTotalPages(response.data.total_pages);
      setCurrentPage(page);
    } catch (error) {
      console.error('Error loading page data:', error);
    }
  };

  const handlePageChange = (event, page) => {
    loadPageData(page);
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
        Data Overview
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Rows
              </Typography>
              <Typography variant="h4">
                {data.shape[0].toLocaleString()}
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
                {data.shape[1]}
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

      <Typography variant="h6" gutterBottom>
        Column Information
      </Typography>
      
      <Box sx={{ mb: 3, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {Object.entries(columnInfo).map(([colName, info]) => (
          <Chip
            key={colName}
            label={`${getTypeIcon(info.type)} ${colName} (${info.type})`}
            color={getTypeColor(info.type)}
            variant={info.has_lists ? "filled" : "outlined"}
            size="small"
          />
        ))}
      </Box>

      <Typography variant="h6" gutterBottom>
        Data Preview
      </Typography>
      
      <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {data.columns.map((column) => (
                <TableCell key={column} sx={{ fontWeight: 'bold', minWidth: 120 }}>
                  <Box>
                    <Typography variant="subtitle2">
                      {column}
                    </Typography>
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
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {pageData.map((row, index) => (
              <TableRow key={index}>
                {data.columns.map((column) => (
                  <TableCell key={column}>
                    <Typography variant="body2" noWrap>
                      {row[column] !== null && row[column] !== undefined 
                        ? String(row[column]) 
                        : <span style={{ color: '#999', fontStyle: 'italic' }}>null</span>
                      }
                    </Typography>
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
        <Pagination
          count={totalPages}
          page={currentPage}
          onChange={handlePageChange}
          color="primary"
          size="large"
        />
      </Box>
    </Box>
  );
};

export default DataPreview;