import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Chip,
  TextField,
  Tooltip
} from '@mui/material';
import {
  ExpandMore,
  FilterList,
  FilterListOff
} from '@mui/icons-material';
import axios from 'axios';
import API_BASE_URL from '../config';
import CategoricalFilter from './filters/CategoricalFilter';
import NumericFilter from './filters/NumericFilter';
import TextFilter from './filters/TextFilter';
import BooleanFilter from './filters/BooleanFilter';
import DateFilter from './filters/DateFilter';

const FILTER_COMPONENTS = {
  categorical: CategoricalFilter,
  numeric: NumericFilter,
  text: TextFilter,
  boolean: BooleanFilter,
  datetime: DateFilter,
};

// One-line, human-readable description of a filter for its chip.
export const describeFilter = (column, filter) => {
  switch (filter?.type) {
    case 'categorical': {
      const values = filter.values || [];
      const shown = values.slice(0, 3).join(', ');
      return `${column}: ${shown}${values.length > 3 ? ` +${values.length - 3} more` : ''}`;
    }
    case 'numeric':
      if (filter.min !== undefined && filter.max !== undefined) return `${column}: ${filter.min} – ${filter.max}`;
      if (filter.min !== undefined) return `${column} ≥ ${filter.min}`;
      return `${column} ≤ ${filter.max}`;
    case 'text': {
      const isRegex = filter.search_type === 'regex';
      const verb = filter.negate
        ? (isRegex ? 'does not match' : 'does not contain')
        : (isRegex ? 'matches' : 'contains');
      return `${column} ${verb} "${filter.value}"`;
    }
    case 'boolean':
      return `${column} = ${filter.value ? 'True' : 'False'}`;
    case 'datetime':
      if (filter.start && filter.end) return `${column}: ${filter.start} → ${filter.end}`;
      if (filter.start) return `${column} from ${filter.start}`;
      return `${column} until ${filter.end}`;
    default:
      return `${column}: filtered`;
  }
};

const sameFilters = (a, b) => JSON.stringify(a || {}) === JSON.stringify(b || {});

const FilterManager = ({ data, columnInfo, onDatasetUpdate, onNotice, onError }) => {
  const appliedFilters = data.active_filters || {};
  // Filters being edited; they take effect on "Apply Filters".
  const [draftFilters, setDraftFilters] = useState(appliedFilters);
  const [expandedPanels, setExpandedPanels] = useState({});
  // Bumping a column's key remounts its editor so local input state resets.
  const [resetKeys, setResetKeys] = useState({});
  const [columnSearch, setColumnSearch] = useState('');
  const [isApplying, setIsApplying] = useState(false);

  // The backend can change the applied filters (new file, sheet switch,
  // column type change); follow it.
  const appliedSignature = JSON.stringify(appliedFilters);
  useEffect(() => {
    setDraftFilters(JSON.parse(appliedSignature));
  }, [appliedSignature]);

  const handleFilterChange = (column, filterConfig) => {
    setDraftFilters((previous) => {
      const next = { ...previous };
      if (filterConfig === null || filterConfig === undefined) {
        delete next[column];
      } else {
        next[column] = filterConfig;
      }
      return next;
    });
  };

  const removeFilter = (column) => {
    handleFilterChange(column, null);
    setResetKeys((previous) => ({ ...previous, [column]: (previous[column] || 0) + 1 }));
  };

  const applyFilters = async () => {
    setIsApplying(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/apply-filters`, {
        filters: draftFilters
      });
      onDatasetUpdate(response.data);
      const { filtered_rows: filteredRows, total_rows: totalRows } = response.data;
      onNotice?.('success', `Filters applied: ${filteredRows.toLocaleString()} of ${totalRows.toLocaleString()} rows match`);
    } catch (error) {
      onError(error.response?.data?.error || 'Failed to apply filters');
    } finally {
      setIsApplying(false);
    }
  };

  const clearAllFilters = async () => {
    setIsApplying(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/clear-filters`);
      setDraftFilters({});
      setResetKeys((previous) => {
        const next = { ...previous };
        Object.keys(columnInfo).forEach((column) => {
          next[column] = (next[column] || 0) + 1;
        });
        return next;
      });
      onDatasetUpdate(response.data);
    } catch (error) {
      onError(error.response?.data?.error || 'Failed to clear filters');
    } finally {
      setIsApplying(false);
    }
  };

  const handlePanelChange = (panel) => (event, isExpanded) => {
    setExpandedPanels(prev => ({
      ...prev,
      [panel]: isExpanded
    }));
  };

  const filterableColumns = Object.entries(columnInfo)
    .filter(([, info]) => FILTER_COMPONENTS[info.type])
    .filter(([column]) => column.toLowerCase().includes(columnSearch.trim().toLowerCase()));

  const draftEntries = Object.entries(draftFilters);
  const isDirty = !sameFilters(draftFilters, appliedFilters);
  const hasAnyFilter = data.has_filters || draftEntries.length > 0;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <FilterList sx={{ mr: 1 }} />
          <Typography variant="h6">
            Data Filters
          </Typography>
          {data.has_filters && (
            <Chip
              size="small"
              label={`${data.filtered_rows.toLocaleString()} / ${data.total_rows.toLocaleString()} rows`}
              color="info"
              variant="outlined"
              sx={{ ml: 1.5 }}
            />
          )}
        </Box>

        <Box>
          <Button
            variant="contained"
            onClick={applyFilters}
            disabled={!isDirty || isApplying}
            sx={{ mr: 1 }}
          >
            Apply Filters
          </Button>
          <Button
            variant="outlined"
            onClick={clearAllFilters}
            disabled={!hasAnyFilter || isApplying}
            startIcon={<FilterListOff />}
          >
            Clear All
          </Button>
        </Box>
      </Box>

      {draftEntries.length > 0 && (
        <Box sx={{ mb: 2 }} data-testid="filter-chips">
          <Typography variant="body2" color={isDirty ? 'warning.main' : 'text.secondary'}>
            {isDirty
              ? 'You have unapplied changes. Press "Apply Filters" to update the data.'
              : `Showing ${data.filtered_rows.toLocaleString()} of ${data.total_rows.toLocaleString()} rows`}
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
            {draftEntries.map(([column, filter]) => (
              <Chip
                key={column}
                size="small"
                label={describeFilter(column, filter)}
                onDelete={() => removeFilter(column)}
                color="primary"
                variant="outlined"
                sx={{ maxWidth: 360 }}
              />
            ))}
          </Box>
        </Box>
      )}

      {draftEntries.length === 0 && isDirty && (
        <Typography variant="body2" color="warning.main" sx={{ mb: 2 }}>
          All filters removed. Press "Apply Filters" to update the data.
        </Typography>
      )}

      {Object.keys(columnInfo).length > 12 && (
        <TextField
          size="small"
          placeholder="Search columns..."
          value={columnSearch}
          onChange={(event) => setColumnSearch(event.target.value)}
          sx={{ mb: 2, minWidth: 260 }}
        />
      )}

      <Box>
        {filterableColumns.map(([column, colInfo]) => {
          const FilterComponent = FILTER_COMPONENTS[colInfo.type];
          return (
            <Accordion
              key={column}
              expanded={expandedPanels[column] || false}
              onChange={handlePanelChange(column)}
              // Mount the editor (and fetch its options) only when opened.
              TransitionProps={{ unmountOnExit: true }}
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
                    {draftFilters[column] && (
                      <Tooltip title="Filter set">
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
                <FilterComponent
                  key={`${column}:${colInfo.type}:${resetKeys[column] || 0}`}
                  column={column}
                  value={draftFilters[column]}
                  onChange={(value) => handleFilterChange(column, value)}
                  onError={onError}
                />
              </AccordionDetails>
            </Accordion>
          );
        })}
        {filterableColumns.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            No filterable columns{columnSearch ? ' match the search' : ''}.
          </Typography>
        )}
      </Box>
    </Box>
  );
};

export default FilterManager;
