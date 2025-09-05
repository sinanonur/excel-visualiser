import React, { useState, useCallback } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Alert,
  Tabs,
  Tab,
  AppBar,
  Toolbar
} from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import FileUpload from './components/FileUpload';
import DataPreview from './components/DataPreview';
import ColumnManager from './components/ColumnManager';
import PlotGenerator from './components/PlotGenerator';
import FilterManager from './components/FilterManager';
import StatisticsViewer from './components/StatisticsViewer';

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

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [data, setData] = useState(null);
  const [columnInfo, setColumnInfo] = useState({});
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [tabValue, setTabValue] = useState(0);

  const handleDataLoad = useCallback((loadedData) => {
    setData(loadedData);
    setColumnInfo(loadedData.column_info);
    setError(null);
    setSuccess('File uploaded and processed successfully!');
    setTimeout(() => setSuccess(null), 3000);
  }, []);

  const handleError = useCallback((errorMessage) => {
    setError(errorMessage);
    setTimeout(() => setError(null), 5000);
  }, []);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleColumnInfoUpdate = (updatedColumnInfo) => {
    setColumnInfo(updatedColumnInfo);
  };

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
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {success}
            </Alert>
          )}

          <Paper elevation={3} sx={{ mb: 3 }}>
            <FileUpload 
              onDataLoad={handleDataLoad} 
              onError={handleError}
            />
          </Paper>

          {data && (
            <Paper elevation={3}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={tabValue} onChange={handleTabChange} aria-label="data exploration tabs">
                  <Tab label="Data Preview" />
                  <Tab label="Column Management" />
                  <Tab label="Filters" />
                  <Tab label="Visualizations" />
                  <Tab label="Statistics" />
                </Tabs>
              </Box>
              
              <TabPanel value={tabValue} index={0}>
                <DataPreview 
                  data={data} 
                  columnInfo={columnInfo}
                />
              </TabPanel>
              
              <TabPanel value={tabValue} index={1}>
                <ColumnManager 
                  data={data}
                  columnInfo={columnInfo}
                  onColumnInfoUpdate={handleColumnInfoUpdate}
                  onError={handleError}
                />
              </TabPanel>
              
              <TabPanel value={tabValue} index={4}>
                <StatisticsViewer
                  columnInfo={columnInfo}
                  onError={handleError}
                />
              </TabPanel>

              <TabPanel value={tabValue} index={2}>
                <FilterManager
                  data={data}
                  columnInfo={columnInfo}
                  onFiltersApplied={() => {
                    // Refresh data preview when filters are applied
                    setSuccess('Filters applied successfully!');
                    setTimeout(() => setSuccess(null), 3000);
                  }}
                  onError={handleError}
                />
              </TabPanel>
              
              <TabPanel value={tabValue} index={3}>
                <PlotGenerator 
                  data={data}
                  columnInfo={columnInfo}
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