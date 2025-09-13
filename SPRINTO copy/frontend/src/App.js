import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import Navigation from './components/Navigation';
import DocumentsPage from './pages/DocumentsPage';
import GitHubPage from './pages/GitHubPage';
import JiraPage from './pages/JiraPage';
import ReportsPage from './pages/ReportsPage';

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
            <Route path="/" element={<DocumentsPage />} />
            <Route path="/github" element={<GitHubPage />} />
            <Route path="/jira" element={<JiraPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Routes>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
