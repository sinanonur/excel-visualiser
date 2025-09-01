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

const FileUpload = ({ onDataLoad, onError }) => {
  const [isUploading, setIsUploading] = React.useState(false);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5001/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (response.data.success) {
        onDataLoad(response.data);
      } else {
        onError(response.data.error || 'Upload failed');
      }
    } catch (error) {
      onError(error.response?.data?.error || 'Network error during upload');
    } finally {
      setIsUploading(false);
    }
  }, [onDataLoad, onError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false,
    disabled: isUploading
  });

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Upload Excel File
      </Typography>
      
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
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
        <input {...getInputProps()} />
        
        {isUploading ? (
          <Box>
            <CircularProgress sx={{ mb: 2 }} />
            <Typography variant="body1">
              Processing your Excel file...
            </Typography>
          </Box>
        ) : (
          <Box>
            <CloudUpload sx={{ fontSize: 64, color: '#1976d2', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop your Excel file here' : 'Drag & drop an Excel file here'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Supports .xlsx and .xls files
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