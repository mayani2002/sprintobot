import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Alert,
  Chip,
  Grid
} from '@mui/material';
import QueryInput from '../components/QueryInput';
import EvidenceResults from '../components/EvidenceResults';
import { evidenceService } from '../services/evidenceService';

const JIRA_SAMPLE_QUERIES = [
  "Show all high-priority tickets assigned to DevOps team",
  "Find tickets without approval workflow",
  "List pending code reviews for the main branch",
  "Show security incidents from last month",
  "Find tickets with missing documentation",
  "Show approval workflow for ticket PROJ-123",
  "List all critical bugs in production",
  "Find tickets assigned to John Doe"
];

const JiraPage = () => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleJiraQuery = async (query) => {
    setLoading(true);
    setResults(null);
    
    try {
      const response = await evidenceService.submitQuery(query, { source: 'jira' });
      setResults(response);
    } catch (error) {
      console.error('JIRA query failed:', error);
      setResults({
        error: true,
        message: 'JIRA query failed. Please check your configuration.'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        JIRA Integration
      </Typography>
      
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Query JIRA for tickets, workflows, approvals, and project management evidence
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Ask JIRA Questions
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Query your JIRA instance to find evidence about tickets, approval workflows, and project activities.
        </Typography>

        <Alert severity="info" sx={{ mb: 3 }}>
          <strong>JIRA Configuration Required:</strong> Make sure your JIRA URL, username, and API token are configured in the backend settings.
        </Alert>
        
        <QueryInput 
          onSubmit={handleJiraQuery}
          loading={loading}
          placeholder="Ask about JIRA tickets, workflows, approvals, or project activity..."
          samples={JIRA_SAMPLE_QUERIES}
        />
        
        {results && (
          <Box sx={{ mt: 3 }}>
            <EvidenceResults results={results} />
          </Box>
        )}
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Sample JIRA Queries
        </Typography>
        
        <Grid container spacing={1}>
          {JIRA_SAMPLE_QUERIES.map((query, index) => (
            <Grid item key={index}>
              <Chip
                label={query}
                variant="outlined"
                onClick={() => handleJiraQuery(query)}
                sx={{ m: 0.5, cursor: 'pointer' }}
              />
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Container>
  );
};

export default JiraPage;
