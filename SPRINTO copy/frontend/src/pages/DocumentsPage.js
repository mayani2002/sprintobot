import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Paper,
  Tab,
  Tabs,
  Alert
} from '@mui/material';
import DocumentUpload from '../components/DocumentUpload';
import DocumentQueryInput from '../components/DocumentQueryInput';
import EvidenceResults from '../components/EvidenceResults';
import { evidenceService } from '../services/evidenceService';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
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

const DocumentsPage = () => {
  const [tabValue, setTabValue] = useState(0);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleDocumentQuery = async (query) => {
    setLoading(true);
    setResults(null);
    
    try {
      const response = await evidenceService.queryDocuments(query);
      setResults(response);
    } catch (error) {
      console.error('Document query failed:', error);
      setResults({
        error: true,
        message: 'Document query failed. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = (result) => {
    setUploadStatus({
      type: 'success',
      message: `Successfully uploaded and parsed ${result.filename}`
    });
    setTimeout(() => setUploadStatus(null), 5000);
  };

  const handleUploadError = (error) => {
    setUploadStatus({
      type: 'error',
      message: `Upload failed: ${error}`
    });
    setTimeout(() => setUploadStatus(null), 5000);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Document Management
      </Typography>
      
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Upload documents and query them using natural language
      </Typography>

      {uploadStatus && (
        <Alert 
          severity={uploadStatus.type} 
          sx={{ mb: 3 }}
          onClose={() => setUploadStatus(null)}
        >
          {uploadStatus.message}
        </Alert>
      )}

      <Paper sx={{ width: '100%', mb: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Upload Documents" />
            <Tab label="Query Documents" />
          </Tabs>
        </Box>
        
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Upload Documents
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Upload CSV, Excel, or PDF files to make them searchable. Supported formats: .csv, .xlsx, .xls, .pdf
          </Typography>
          <DocumentUpload 
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Search Documents
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Ask questions about your uploaded documents using natural language.
          </Typography>
          
          <DocumentQueryInput 
            onSubmit={handleDocumentQuery}
            loading={loading}
          />
          
          {results && (
            <Box sx={{ mt: 3 }}>
              {results.error ? (
                <Alert severity="error">
                  {results.message}
                </Alert>
              ) : (
                <EvidenceResults 
                  result={results} 
                  onExport={(queryId, format) => evidenceService.exportEvidence(queryId, format)}
                />
              )}
            </Box>
          )}
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default DocumentsPage;
