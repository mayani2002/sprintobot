import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import Navigation from './components/Navigation';
import DocumentsPage from './pages/DocumentsPage';
import GitHubPage from './pages/GitHubPage';
import JiraPage from './pages/JiraPage';
import ReportsPage from './pages/ReportsPage';
import LandingPage from './components/LandingPage';
// import IncidentInvestigation from './components/IncidentInvestigation';
// import AIQueryAssistant from './components/AIQueryAssistant';
// import './App.css';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <Navigation />
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/github-audit" element={<GitHubPage />} />
            <Route path="/jira-compliance" element={<JiraPage />} />
            <Route path="/document-analysis" element={<DocumentsPage />} />
            {/* <Route path="/incident-investigation" element={<IncidentInvestigation />} /> */}
            <Route path="/compliance-report" element={<ReportsPage />} />
            {/* <Route path="/ai-query" element={<AIQueryAssistant />} /> */}
          </Routes>
        </Box>
      </Router>
    </ThemeProvider>
  );
}


export default App;
