import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Tabs,
  Tab
} from '@mui/material';
import {
  Description as DocumentIcon,
  GitHub as GitHubIcon,
  BugReport as JiraIcon,
  Assessment as ReportIcon
} from '@mui/icons-material';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const tabs = [
    { label: 'Documents', value: '/', icon: <DocumentIcon /> },
    { label: 'GitHub', value: '/github', icon: <GitHubIcon /> },
    { label: 'JIRA', value: '/jira', icon: <JiraIcon /> },
    { label: 'Reports', value: '/reports', icon: <ReportIcon /> }
  ];

  const handleTabChange = (event, newValue) => {
    navigate(newValue);
  };

  const currentTab = tabs.find(tab => tab.value === location.pathname)?.value || '/';

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          AI-Powered Evidence-on-Demand Bot
        </Typography>
        
        <Box sx={{ ml: 'auto' }}>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            textColor="inherit"
            indicatorColor="secondary"
          >
            {tabs.map((tab) => (
              <Tab
                key={tab.value}
                label={tab.label}
                value={tab.value}
                icon={tab.icon}
                iconPosition="start"
                sx={{ 
                  color: 'white',
                  '&.Mui-selected': {
                    color: 'white'
                  }
                }}
              />
            ))}
          </Tabs>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;
