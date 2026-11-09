import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Alert,
  Tabs,
  Tab,
  AppBar,
  Toolbar,
  Chip,
  Button,
  Menu,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  CircularProgress
} from '@mui/material';
import { Download, FilterList } from '@mui/icons-material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import axios from 'axios';
import API_BASE_URL from './config';
import FileUpload from './components/FileUpload';
import DataPreview from './components/DataPreview';
import DataProfile from './components/DataProfile';
import ColumnManager from './components/ColumnManager';
import PlotGenerator from './components/PlotGenerator';
import FilterManager from './components/FilterManager';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const PLOT_TAB = 4;

function TabPanel(props) {
  const { children, value, index, keepMounted = false, ...other } = props;
  const active = value === index;

  return (
    <div
      role="tabpanel"
      hidden={!active}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {(active || keepMounted) && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const EXPORT_OPTIONS = [
  { format: 'csv', scope: 'filtered', label: 'CSV', filteredLabel: 'CSV (filtered rows)' },
  { format: 'xlsx', scope: 'filtered', label: 'Excel', filteredLabel: 'Excel (filtered rows)' },
  { format: 'csv', scope: 'all', filteredLabel: 'CSV (all rows)', onlyWhenFiltered: true },
];

function App() {
  // Dataset state mirrored from the backend: columns, column_info, shape,
  // file_name, sheet_names, active_sheet and the filter status.
  const [dataset, setDataset] = useState(null);
  // Bumped whenever the backend data changes so data-driven views reload.
  const [refreshKey, setRefreshKey] = useState(0);
  const [notice, setNotice] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [backendDown, setBackendDown] = useState(false);
  const [restoring, setRestoring] = useState(true);
  const [exportAnchor, setExportAnchor] = useState(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isSwitchingSheet, setIsSwitchingSheet] = useState(false);
  const noticeTimer = useRef(null);

  const notify = useCallback((severity, message) => {
    clearTimeout(noticeTimer.current);
    setNotice({ severity, message });
    noticeTimer.current = setTimeout(() => setNotice(null), severity === 'success' ? 3000 : 7000);
  }, []);

  const handleError = useCallback((message) => notify('error', message), [notify]);

  // Merge any backend response that carries dataset state into ours.
  const applyDatasetState = useCallback((payload) => {
    setDataset((previous) => ({
      ...(previous || {}),
      columns: payload.columns ?? previous?.columns ?? [],
      column_info: payload.column_info ?? previous?.column_info ?? {},
      shape: payload.shape ?? previous?.shape ?? [0, 0],
      file_name: payload.file_name ?? previous?.file_name ?? null,
      sheet_names: payload.sheet_names ?? previous?.sheet_names ?? [],
      active_sheet: payload.active_sheet ?? previous?.active_sheet ?? null,
      has_filters: payload.has_filters ?? previous?.has_filters ?? false,
      active_filters: payload.active_filters ?? previous?.active_filters ?? {},
      filtered_rows: payload.filtered_rows ?? previous?.filtered_rows ?? 0,
      total_rows: payload.total_rows ?? previous?.total_rows ?? 0,
    }));
    setRefreshKey((key) => key + 1);
  }, []);

  const restoreSession = useCallback(async () => {
    setRestoring(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/session`);
      setBackendDown(false);
      if (response.data.loaded) {
        applyDatasetState(response.data);
      }
    } catch (error) {
      setBackendDown(true);
    } finally {
      setRestoring(false);
    }
  }, [applyDatasetState]);

  // The backend keeps the dataset in memory, so a page reload can resume it.
  useEffect(() => {
    restoreSession();
    return () => clearTimeout(noticeTimer.current);
  }, [restoreSession]);

  const handleDataLoad = useCallback((loadedData) => {
    applyDatasetState(loadedData);
    setBackendDown(false);
    setTabValue(0);
    notify('success', 'File uploaded and processed successfully!');
  }, [applyDatasetState, notify]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    if (newValue === PLOT_TAB) {
      // The plot stays mounted while hidden; let Plotly re-measure its container.
      setTimeout(() => window.dispatchEvent(new Event('resize')), 0);
    }
  };

  const handleSheetChange = async (sheet) => {
    setIsSwitchingSheet(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/select-sheet`, { sheet });
      applyDatasetState(response.data);
      notify('success', `Switched to sheet "${sheet}"`);
    } catch (error) {
      handleError(error.response?.data?.error || 'Failed to switch sheet');
    } finally {
      setIsSwitchingSheet(false);
    }
  };

  const handleExport = async ({ format, scope }) => {
    setExportAnchor(null);
    setIsExporting(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/export`, {
        params: { format, scope },
        responseType: 'blob',
      });
      const disposition = response.headers['content-disposition'] || '';
      const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition);
      const filename = match ? decodeURIComponent(match[1]) : `export.${format}`;
      const url = URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      let message = 'Export failed';
      if (error.response?.data instanceof Blob) {
        try {
          message = JSON.parse(await error.response.data.text()).error || message;
        } catch (parseError) {
          // keep the generic message
        }
      }
      handleError(message);
    } finally {
      setIsExporting(false);
    }
  };

  const columnInfo = dataset?.column_info || {};
  const exportOptions = EXPORT_OPTIONS.filter((option) => dataset?.has_filters || !option.onlyWhenFiltered);

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Excel Data Science Visualizer
            </Typography>
          </Toolbar>
        </AppBar>

        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          {backendDown && (
            <Alert
              severity="warning"
              sx={{ mb: 2 }}
              action={<Button color="inherit" size="small" onClick={restoreSession}>Retry</Button>}
            >
              Cannot reach the backend at {API_BASE_URL}. Start it and retry.
            </Alert>
          )}

          {notice && (
            <Alert severity={notice.severity} sx={{ mb: 2 }} onClose={() => setNotice(null)}>
              {notice.message}
            </Alert>
          )}

          <Paper elevation={3} sx={{ mb: 3 }}>
            <FileUpload
              onDataLoad={handleDataLoad}
              onError={handleError}
              currentFile={dataset?.file_name}
            />
          </Paper>

          {restoring && !dataset && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress size={24} />
            </Box>
          )}

          {dataset && (
            <Paper elevation={3}>
              <Box
                sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1.5, px: 3, pt: 2 }}
                data-testid="dataset-bar"
              >
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }} noWrap title={dataset.file_name || ''}>
                  {dataset.file_name || 'Dataset'}
                </Typography>

                {dataset.sheet_names.length > 1 && (
                  <FormControl size="small" sx={{ minWidth: 160 }} disabled={isSwitchingSheet}>
                    <InputLabel id="sheet-select-label">Sheet</InputLabel>
                    <Select
                      labelId="sheet-select-label"
                      label="Sheet"
                      value={dataset.active_sheet || ''}
                      onChange={(event) => handleSheetChange(event.target.value)}
                    >
                      {dataset.sheet_names.map((sheet) => (
                        <MenuItem key={sheet} value={sheet}>{sheet}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}

                <Chip
                  size="small"
                  icon={dataset.has_filters ? <FilterList /> : undefined}
                  color={dataset.has_filters ? 'info' : 'default'}
                  variant="outlined"
                  label={dataset.has_filters
                    ? `${dataset.filtered_rows.toLocaleString()} of ${dataset.total_rows.toLocaleString()} rows (filtered)`
                    : `${dataset.total_rows.toLocaleString()} rows × ${dataset.shape[1]} columns`}
                />

                <Box sx={{ flexGrow: 1 }} />

                <Button
                  size="small"
                  variant="outlined"
                  startIcon={isExporting ? <CircularProgress size={16} /> : <Download />}
                  onClick={(event) => setExportAnchor(event.currentTarget)}
                  disabled={isExporting}
                >
                  Export
                </Button>
                <Menu anchorEl={exportAnchor} open={Boolean(exportAnchor)} onClose={() => setExportAnchor(null)}>
                  {exportOptions.map((option) => (
                    <MenuItem key={`${option.format}-${option.scope}`} onClick={() => handleExport(option)}>
                      {dataset.has_filters ? option.filteredLabel : option.label}
                    </MenuItem>
                  ))}
                </Menu>
              </Box>

              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs
                  value={tabValue}
                  onChange={handleTabChange}
                  aria-label="data exploration tabs"
                  variant="scrollable"
                  scrollButtons="auto"
                >
                  <Tab label="Data Preview" />
                  <Tab label="Profile" />
                  <Tab label="Column Management" />
                  <Tab label="Filters" />
                  <Tab label="Visualizations" />
                </Tabs>
              </Box>

              <TabPanel value={tabValue} index={0}>
                <DataPreview
                  data={dataset}
                  columnInfo={columnInfo}
                  refreshKey={refreshKey}
                  onError={handleError}
                />
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                <DataProfile refreshKey={refreshKey} onError={handleError} />
              </TabPanel>

              <TabPanel value={tabValue} index={2}>
                <ColumnManager
                  columnInfo={columnInfo}
                  onDatasetUpdate={applyDatasetState}
                  onNotice={notify}
                  onError={handleError}
                />
              </TabPanel>

              <TabPanel value={tabValue} index={3}>
                <FilterManager
                  data={dataset}
                  columnInfo={columnInfo}
                  onDatasetUpdate={applyDatasetState}
                  onNotice={notify}
                  onError={handleError}
                />
              </TabPanel>

              <TabPanel value={tabValue} index={PLOT_TAB} keepMounted>
                <PlotGenerator
                  data={dataset}
                  columnInfo={columnInfo}
                  refreshKey={refreshKey}
                  onError={handleError}
                />
              </TabPanel>
            </Paper>
          )}
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
