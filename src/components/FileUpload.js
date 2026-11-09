import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress
} from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import axios from 'axios';
import API_BASE_URL from '../config';

const ACCEPTED_EXTENSIONS = ['.xlsx', '.xls', '.xlsm', '.csv', '.tsv'];

const FileUpload = ({ onDataLoad, onError, currentFile }) => {
  const [isUploading, setIsUploading] = React.useState(false);

  const onDrop = useCallback(async (acceptedFiles, rejectedFiles) => {
    const file = acceptedFiles[0];
    if (!file) {
      if (rejectedFiles && rejectedFiles.length > 0) {
        onError(`Unsupported file. Use one of: ${ACCEPTED_EXTENSIONS.join(', ')}`);
      }
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData);

      if (response.data.success) {
        onDataLoad(response.data);
      } else {
        onError(response.data.error || 'Upload failed');
      }
    } catch (error) {
      onError(error.response?.data?.error
        || (error.response ? 'Upload failed' : `Cannot reach the backend at ${API_BASE_URL}`));
    } finally {
      setIsUploading(false);
    }
  }, [onDataLoad, onError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.ms-excel.sheet.macroEnabled.12': ['.xlsm'],
      'text/csv': ['.csv'],
      'text/tab-separated-values': ['.tsv']
    },
    multiple: false,
    disabled: isUploading
  });

  // Once a dataset is loaded the dropzone shrinks so the data gets the space.
  const compact = Boolean(currentFile);

  return (
    <Box sx={{ p: compact ? 2 : 3 }}>
      {!compact && (
        <Typography variant="h5" gutterBottom>
          Upload Data File
        </Typography>
      )}

      <Paper
        {...getRootProps()}
        sx={{
          p: compact ? 1.5 : 4,
          textAlign: 'center',
          cursor: isUploading ? 'not-allowed' : 'pointer',
          border: isDragActive ? '2px dashed #1976d2' : '2px dashed #ccc',
          backgroundColor: isDragActive ? '#f3f7ff' : '#fafafa',
          transition: 'all 0.3s ease',
          '&:hover': {
            backgroundColor: isUploading ? '#fafafa' : '#f0f0f0',
            borderColor: isUploading ? '#ccc' : '#1976d2'
          }
        }}
      >
        <input {...getInputProps()} data-testid="file-input" />

        {isUploading ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
            <CircularProgress size={compact ? 20 : 40} />
            <Typography variant="body1">
              Processing your file...
            </Typography>
          </Box>
        ) : compact ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1.5, flexWrap: 'wrap' }}>
            <CloudUpload sx={{ color: '#1976d2' }} />
            <Typography variant="body2" color="text.secondary">
              {isDragActive
                ? 'Drop to replace the current dataset'
                : 'Drag & drop or click to load a different file (.xlsx, .xls, .csv, .tsv)'}
            </Typography>
          </Box>
        ) : (
          <Box>
            <CloudUpload sx={{ fontSize: 64, color: '#1976d2', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop your file here' : 'Drag & drop an Excel or CSV file here'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Supports .xlsx, .xls, .xlsm, .csv and .tsv files
            </Typography>
            <Button variant="outlined" component="span">
              Or click to browse files
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default FileUpload;
