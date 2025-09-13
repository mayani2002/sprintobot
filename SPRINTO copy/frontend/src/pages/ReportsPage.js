import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  Alert,
  IconButton,
  Collapse,
  CircularProgress
} from '@mui/material';
import {
  Description as TextIcon,
  Code as JsonIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { evidenceService } from '../services/evidenceService';

const ReportsPage = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [expandedReport, setExpandedReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    setFetching(true);
    setError(null);
    try {
      const response = await evidenceService.getReports();
      setReports(response.reports || []);
    } catch (err) {
      console.error('Failed to fetch reports:', err);
      setError('Failed to load reports. Please try again.');
      // Fallback to empty array
      setReports([]);
    } finally {
      setFetching(false);
    }
  };

  const handleExport = async (reportId, format) => {
    setLoading(true);
    try {
      console.log(`Starting export for report ${reportId} in ${format} format`);
      
      // Export from backend
      const blob = await evidenceService.exportReport(reportId, format);
      
      if (!blob) {
        throw new Error('Failed to generate report blob');
      }
      
      console.log(`Generated blob of size: ${blob.size} bytes, type: ${blob.type}`);
      
      // Create download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `evidence_report_${reportId}_${new Date().toISOString().split('T')[0]}.${format}`;
      
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);
      
      console.log('Export completed successfully');
      
    } catch (error) {
      console.error('Export failed:', error);
      alert(`Export failed: ${error.message}. Please try again or contact support.`);
    } finally {
      setLoading(false);
    }
  };


  const toggleExpanded = (reportId) => {
    setExpandedReport(expandedReport === reportId ? null : reportId);
  };

  const getSourceColor = (source) => {
    const colors = {
      documents: 'primary',
      github: 'secondary',
      jira: 'success'
    };
    return colors[source] || 'default';
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Evidence Reports
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Generate, view, and export comprehensive evidence reports
          </Typography>
        </Box>
        <Button
          startIcon={<RefreshIcon />}
          onClick={fetchReports}
          disabled={fetching}
          variant="outlined"
        >
          {fetching ? <CircularProgress size={20} /> : 'Refresh'}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Alert severity="info" sx={{ mb: 3 }}>
        <strong>Report Generation:</strong> Reports are automatically generated from your queries and can be exported in TXT or JSON formats.
      </Alert>

      <Grid container spacing={3}>
        {reports.map((report) => (
          <Grid item xs={12} key={report.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Box flex={1}>
                    <Typography variant="h6" component="h2">
                      {report.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {report.description}
                    </Typography>
                    
                    <Box display="flex" gap={1} mb={2}>
                      {report.sources.map((source) => (
                        <Chip
                          key={source}
                          label={source}
                          color={getSourceColor(source)}
                          size="small"
                        />
                      ))}
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary">
                      Generated: {new Date(report.created_at).toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Evidence Count: {report.evidence_count} items
                    </Typography>
                  </Box>
                  
                  <IconButton
                    onClick={() => toggleExpanded(report.id)}
                    sx={{ ml: 2 }}
                  >
                    {expandedReport === report.id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                </Box>

                <Collapse in={expandedReport === report.id}>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Summary:
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {report.summary}
                    </Typography>
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Related Queries:
                    </Typography>
                    <ul>
                      {report.queries.map((query, index) => (
                        <li key={index}>
                          <Typography variant="body2">{query}</Typography>
                        </li>
                      ))}
                    </ul>
                  </Box>
                </Collapse>
              </CardContent>
              
              <CardActions>
                <Button
                  startIcon={<TextIcon />}
                  onClick={() => handleExport(report.id, 'txt')}
                  disabled={loading}
                  size="small"
                >
                  Export Text
                </Button>
                <Button
                  startIcon={<JsonIcon />}
                  onClick={() => handleExport(report.id, 'json')}
                  disabled={loading}
                  size="small"
                >
                  Export JSON
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {reports.length === 0 && !fetching && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No reports generated yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Start by running queries on the Documents, GitHub, or JIRA pages to generate reports.
          </Typography>
          <Button
            variant="contained"
            onClick={fetchReports}
            sx={{ mt: 2 }}
            startIcon={<RefreshIcon />}
          >
            Refresh Reports
          </Button>
        </Paper>
      )}

      {fetching && reports.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <CircularProgress sx={{ mb: 2 }} />
          <Typography variant="body2" color="text.secondary">
            Loading reports...
          </Typography>
        </Paper>
      )}
    </Container>
  );
};

export default ReportsPage;
