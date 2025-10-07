import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  Chip,
  CircularProgress
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const SAMPLE_QUERIES = [
  "How many PRs were merged without approval?",
  "Show me all PRs approved by Alice?",
  "List PRs waiting for review from 24hours",
  "Which PRs were merged in the last 7 days, and who approved them?",
];

const QueryInput = ({ onSubmit, loading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSubmit(query.trim());
    }
  };

  const handleSampleQuery = (sampleQuery) => {
    setQuery(sampleQuery);
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <TextField
        fullWidth
        multiline
        rows={3}
        variant="outlined"
        placeholder="Ask about GitHub PRs, JIRA tickets, or uploaded documents...

Examples:
• How many PRs were merged without approval?
• Show me all PRs approved by Alice?
• List PRs waiting for review from 24hour"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        disabled={loading}
        sx={{ mb: 2 }}
      />

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Button
          type="submit"
          variant="contained"
          size="large"
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          disabled={!query.trim() || loading}
        >
          {loading ? 'Processing...' : 'Get Evidence'}
        </Button>
      </Box>

      <Paper elevation={1} sx={{ p: 2, backgroundColor: '#f8f9fa' }}>
        <Typography variant="subtitle2" gutterBottom>
          Try these sample queries:
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {SAMPLE_QUERIES.map((sampleQuery, index) => (
            <Chip
              key={index}
              label={sampleQuery}
              onClick={() => handleSampleQuery(sampleQuery)}
              variant="outlined"
              size="small"
              sx={{ 
                cursor: 'pointer',
                '&:hover': { backgroundColor: 'primary.light', color: 'primary.contrastText' }
              }}
            />
          ))}
        </Box>
      </Paper>
    </Box>
  );
};

export default QueryInput;
