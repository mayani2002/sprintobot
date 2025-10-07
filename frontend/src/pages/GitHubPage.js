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

const GITHUB_SAMPLE_QUERIES = [
  "How many PRs were merged without approval?",
  "Show me all PRs approved by Alice?",
  "List PRs waiting for review from 24hours",
  "Which PRs were merged in the last 7 days, and who approved them?",
];

const GitHubPage = () => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGitHubQuery = async (query) => {
    setLoading(true);
    setResults(null);
    
    try {
      const response = await evidenceService.submitQuery(query, "github")
      setResults(response);
    } catch (error) {
      console.error('GitHub query failed:', error);
      setResults({
        error: true,
        message: 'GitHub query failed. Please check your configuration.'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        GitHub Integration
      </Typography>
      
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Query GitHub repositories for pull requests, code reviews, and approval workflows
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Ask GitHub Questions
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Query your GitHub repositories to find evidence about pull requests, approvals, and code reviews.
        </Typography>

        <Alert severity="info" sx={{ mb: 3 }}>
          <strong>GitHub Token Required:</strong> Make sure your GitHub token is configured in the backend settings.
        </Alert>
        
        <QueryInput 
          onSubmit={handleGitHubQuery}
          loading={loading}
          placeholder="Ask about GitHub PRs, code reviews, approvals, or repository activity..."
          samples={GITHUB_SAMPLE_QUERIES}
        />
        
        {results && (
          <Box sx={{ mt: 3 }}>
            <EvidenceResults results={results} />
          </Box>
        )}
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Sample GitHub Queries
        </Typography>
        
        <Grid container spacing={1}>
          {GITHUB_SAMPLE_QUERIES.map((query, index) => (
            <Grid item key={index}>
              <Chip
                label={query}
                variant="outlined"
                onClick={() => handleGitHubQuery(query)}
                sx={{ m: 0.5, cursor: 'pointer' }}
              />
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Container>
  );
};

export default GitHubPage;
