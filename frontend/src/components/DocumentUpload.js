import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  LinearProgress
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  InsertDriveFile as FileIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

const DocumentUpload = () => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = async (acceptedFiles) => {
    setUploading(true);
    setError(null);

    try {
      for (const file of acceptedFiles) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/v1/evidence/documents/upload', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const result = await response.json();
        
        setUploadedFiles(prev => [...prev, {
          id: Date.now() + Math.random(),
          name: file.name,
          size: file.size,
          type: file.type,
          uploadResult: result,
          status: 'completed'
        }]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv']
    },
    disabled: uploading
  });

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box>
      <Box
        {...getRootProps()}
        sx={{
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          borderRadius: 2,
          p: 4,
          textAlign: 'center',
          cursor: uploading ? 'not-allowed' : 'pointer',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'action.hover'
          }
        }}
      >
        <input {...getInputProps()} />
        <UploadIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          or click to browse files
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Supported formats: PDF, Excel (.xlsx, .xls), CSV
        </Typography>
        <br />
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          sx={{ mt: 2 }}
          disabled={uploading}
        >
          Choose Files
        </Button>
      </Box>

      {uploading && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" gutterBottom>
            Uploading and processing files...
          </Typography>
          <LinearProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {uploadedFiles.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Uploaded Files ({uploadedFiles.length})
          </Typography>
          <List>
            {uploadedFiles.map((file) => (
              <ListItem
                key={file.id}
                sx={{
                  border: '1px solid',
                  borderColor: 'grey.200',
                  borderRadius: 1,
                  mb: 1
                }}
              >
                <ListItemIcon>
                  {file.status === 'completed' ? (
                    <CheckIcon color="success" />
                  ) : (
                    <FileIcon />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={file.name}
                  secondary={`${formatFileSize(file.size)} • ${file.status}`}
                />
                <IconButton
                  edge="end"
                  onClick={() => removeFile(file.id)}
                  size="small"
                >
                  <DeleteIcon />
                </IconButton>
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      <Alert severity="info" sx={{ mt: 2 }}>
        <Typography variant="body2">
          <strong>Note:</strong> Uploaded documents will be parsed and made searchable.
          You can then ask questions like "Find all invoices from vendor XYZ" or 
          "Show asset count for laptops".
        </Typography>
      </Alert>
    </Box>
  );
};

export default DocumentUpload;
