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
import FindInPageIcon from '@mui/icons-material/FindInPage';

const SAMPLE_DOCUMENT_QUERIES = [
  "Show the current count of laptops in the office",
  "Find all Apple devices in the asset register",
  "List assets assigned to John Doe",
  "Show all equipment on Office Floor 1",
  "Find assets with warranty expiring in 2026",
  "Count all Dell laptops"
];

const DocumentQueryInput = ({ onSubmit, loading }) => {
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
        placeholder="Ask questions about your uploaded documents...

Examples:
• Show the current count of laptops in the office
• Find all Apple devices in the asset register
• List assets assigned to specific employees"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        disabled={loading}
        sx={{ mb: 3 }}
      />

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Try these sample queries:
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {SAMPLE_DOCUMENT_QUERIES.map((sampleQuery, index) => (
            <Chip
              key={index}
              label={sampleQuery}
              onClick={() => handleSampleQuery(sampleQuery)}
              variant="outlined"
              size="small"
              sx={{ 
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: 'primary.light',
                  color: 'white'
                }
              }}
            />
          ))}
        </Box>
      </Box>

      <Button
        type="submit"
        variant="contained"
        startIcon={loading ? <CircularProgress size={20} /> : <FindInPageIcon />}
        disabled={!query.trim() || loading}
        fullWidth
        size="large"
      >
        {loading ? 'Searching Documents...' : 'Search Documents'}
      </Button>
    </Box>
  );
};

export default DocumentQueryInput;
