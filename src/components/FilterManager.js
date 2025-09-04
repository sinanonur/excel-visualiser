import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Chip,
  Badge,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ExpandMore,
  FilterList,
  FilterListOff,
  Clear
} from '@mui/icons-material';
import axios from 'axios';
import API_BASE_URL from '../config';
import CategoricalFilter from './filters/CategoricalFilter';
import NumericFilter from './filters/NumericFilter';
import TextFilter from './filters/TextFilter';
import BooleanFilter from './filters/BooleanFilter';

const FilterManager = ({ data, columnInfo, onFiltersApplied, onError }) => {
  const [activeFilters, setActiveFilters] = useState({});
  const [filterStats, setFilterStats] = useState({
    filtered_rows: 0,
    total_rows: 0,
    has_filters: false
  });
  const [expandedPanels, setExpandedPanels] = useState({});

  useEffect(() => {
    loadFilterStatus();
  }, [data]);

  const loadFilterStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/filter-status`);
      const status = response.data;
      setFilterStats(status);
      setActiveFilters(status.active_filters || {});
    } catch (error) {
      console.error('Error loading filter status:', error);
    }
  };

  const handleFilterChange = (column, filterConfig) => {
    const newFilters = { ...activeFilters };
    
    if (filterConfig === null || filterConfig === undefined) {
      // Remove filter
      delete newFilters[column];
    } else {
      // Add/update filter
      newFilters[column] = filterConfig;
    }
    
    setActiveFilters(newFilters);
  };

  const applyFilters = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/apply-filters`, {
        filters: activeFilters
      });
      
      if (response.data.success) {
        setFilterStats({
          filtered_rows: response.data.filtered_rows,
          total_rows: response.data.total_rows,
          has_filters: Object.keys(activeFilters).length > 0
        });
        onFiltersApplied && onFiltersApplied(response.data);
      }
    } catch (error) {
      onError('Failed to apply filters');
      console.error('Error applying filters:', error);
    }
  };

  const clearAllFilters = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/clear-filters`);
      
      if (response.data.success) {
        setActiveFilters({});
        setFilterStats({
          filtered_rows: response.data.total_rows,
          total_rows: response.data.total_rows,
          has_filters: false
        });
        onFiltersApplied && onFiltersApplied(response.data);
      }
    } catch (error) {
      onError('Failed to clear filters');
      console.error('Error clearing filters:', error);
    }
  };

  const handlePanelChange = (panel) => (event, isExpanded) => {
    setExpandedPanels(prev => ({
      ...prev,
      [panel]: isExpanded
    }));
  };

  const renderFilter = (column, colInfo) => {
    const filterType = colInfo.type;
    
    switch (filterType) {
      case 'categorical':
        return (
          <CategoricalFilter
            column={column}
            value={activeFilters[column]}
            onChange={(value) => handleFilterChange(column, value)}
            onError={onError}
          />
        );
      
      case 'numeric':
        return (
          <NumericFilter
            column={column}
            value={activeFilters[column]}
            onChange={(value) => handleFilterChange(column, value)}
            onError={onError}
          />
        );
      
      case 'text':
        return (
          <TextFilter
            column={column}
            value={activeFilters[column]}
            onChange={(value) => handleFilterChange(column, value)}
            onError={onError}
          />
        );
      
      case 'boolean':
        return (
          <BooleanFilter
            column={column}
            value={activeFilters[column]}
            onChange={(value) => handleFilterChange(column, value)}
            onError={onError}
          />
        );
      
      default:
        return (
          <Typography variant="body2" color="text.secondary">
            Filtering not available for this column type
          </Typography>
        );
    }
  };

  const getFilterableColumns = () => {
    return Object.entries(columnInfo).filter(([col, info]) =>
      ['categorical', 'numeric', 'text', 'boolean'].includes(info.type)
    );
  };

  const filterableColumns = getFilterableColumns();

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <FilterList sx={{ mr: 1 }} />
          <Typography variant="h6">
            Data Filters
          </Typography>
          {filterStats.has_filters && (
            <Badge
              badgeContent={Object.keys(activeFilters).length}
              color="primary"
              sx={{ ml: 1 }}
            >
              <Chip
                size="small"
                label={`${filterStats.filtered_rows}/${filterStats.total_rows} rows`}
                color="info"
                variant="outlined"
              />
            </Badge>
          )}
        </Box>
        
        <Box>
          <Button
            variant="contained"
            onClick={applyFilters}
            disabled={Object.keys(activeFilters).length === 0}
            sx={{ mr: 1 }}
          >
            Apply Filters
          </Button>
          <Button
            variant="outlined"
            onClick={clearAllFilters}
            disabled={!filterStats.has_filters}
            startIcon={<FilterListOff />}
          >
            Clear All
          </Button>
        </Box>
      </Box>

      {filterStats.has_filters && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Showing {filterStats.filtered_rows.toLocaleString()} of {filterStats.total_rows.toLocaleString()} rows
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
            {Object.entries(activeFilters).map(([column, filter]) => (
              <Chip
                key={column}
                size="small"
                label={`${column}: filtered`}
                onDelete={() => handleFilterChange(column, null)}
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      )}

      <Box>
        {filterableColumns.map(([column, colInfo]) => (
          <Accordion
            key={column}
            expanded={expandedPanels[column] || false}
            onChange={handlePanelChange(column)}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                <Typography sx={{ flexGrow: 1 }}>
                  {column}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                  <Chip
                    size="small"
                    label={colInfo.type}
                    color="default"
                    variant="outlined"
                    sx={{ mr: 1 }}
                  />
                  {activeFilters[column] && (
                    <Tooltip title="Filter active">
                      <Chip
                        size="small"
                        label="●"
                        color="primary"
                      />
                    </Tooltip>
                  )}
                </Box>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {renderFilter(column, colInfo)}
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    </Box>
  );
};

export default FilterManager;