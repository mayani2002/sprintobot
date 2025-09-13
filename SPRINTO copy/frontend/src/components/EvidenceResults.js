import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Divider,
  Alert
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  GitHub as GitHubIcon,
  Description as JiraIcon,
  InsertDriveFile as DocumentIcon,
  Download as DownloadIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import ReactJson from '@microlink/react-json-view';

const getSourceIcon = (sourceType) => {
  switch (sourceType) {
    case 'github':
      return <GitHubIcon />;
    case 'jira':
      return <JiraIcon />;
    case 'document':
      return <DocumentIcon />;
    default:
      return <DocumentIcon />;
  }
};

const getSourceColor = (sourceType) => {
  switch (sourceType) {
    case 'github':
      return 'primary';
    case 'jira':
      return 'info';
    case 'document':
      return 'warning';
    default:
      return 'default';
  }
};

const EvidenceItem = ({ evidence }) => {
  const [expanded, setExpanded] = useState(false);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Chip
            icon={getSourceIcon(evidence.source_type)}
            label={evidence.source}
            color={getSourceColor(evidence.source_type)}
            size="small"
            sx={{ mr: 2 }}
          />
          <Chip
            label={`${(evidence.confidence_score * 100).toFixed(0)}% confidence`}
            color={getConfidenceColor(evidence.confidence_score)}
            size="small"
            variant="outlined"
          />
        </Box>

        <Typography variant="h6" gutterBottom>
          {evidence.title}
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {evidence.description}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          {evidence.timestamp && (
            <Chip
              icon={<ScheduleIcon />}
              label={formatTimestamp(evidence.timestamp)}
              size="small"
              variant="outlined"
            />
          )}
          {evidence.data?.user && (
            <Chip
              icon={<PersonIcon />}
              label={evidence.data.user}
              size="small"
              variant="outlined"
            />
          )}
        </Box>

        <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="body2">View detailed data</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <ReactJson
              src={evidence.data}
              collapsed={2}
              displayDataTypes={false}
              displayObjectSize={false}
              enableClipboard={false}
              theme="rjv-default"
            />
          </AccordionDetails>
        </Accordion>
      </CardContent>
    </Card>
  );
};

const EvidenceResults = ({ result, onExport }) => {
  // Add null checks to prevent undefined errors
  if (!result) {
    return null;
  }

  const evidenceBySource = result.evidence?.reduce((acc, item) => {
    const source = item.source_type || 'unknown';
    if (!acc[source]) acc[source] = [];
    acc[source].push(item);
    return acc;
  }, {}) || {};

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Evidence Summary
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Query:</strong> {result.query || 'Unknown query'}
        </Typography>
        <Typography variant="body2">
          <strong>Found:</strong> {result.evidence?.length || 0} pieces of evidence
        </Typography>
        <Typography variant="body2">
          <strong>Query ID:</strong> {result.query_id}
        </Typography>
      </Alert>

      {result.message && (
        <Card sx={{ mb: 3, backgroundColor: '#f8f9fa' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              AI Analysis
            </Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {result.message}
            </Typography>
          </CardContent>
        </Card>
      )}

      <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => onExport(result.query_id, 'json')}
        >
          Export JSON
        </Button>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => onExport(result.query_id, 'csv')}
        >
          Export CSV
        </Button>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => onExport(result.query_id, 'xlsx')}
        >
          Export Excel
        </Button>
      </Box>

      {result.evidence && result.evidence.length > 0 ? (
        <Grid container spacing={3}>
          {Object.entries(evidenceBySource).map(([source, items]) => (
            <Grid item xs={12} key={source}>
              <Typography variant="h6" sx={{ mb: 2, textTransform: 'capitalize' }}>
                {source} Evidence ({items.length})
              </Typography>
              {items.map((evidence, index) => (
                <EvidenceItem key={index} evidence={evidence} />
              ))}
              {source !== Object.keys(evidenceBySource)[Object.keys(evidenceBySource).length - 1] && (
                <Divider sx={{ my: 3 }} />
              )}
            </Grid>
          ))}
        </Grid>
      ) : (
        <Alert severity="warning">
          No evidence found for your query. Try rephrasing your question or check your integrations.
        </Alert>
      )}
    </Box>
  );
};

export default EvidenceResults;
