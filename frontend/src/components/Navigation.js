import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  useTheme,
  useMediaQuery,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  Menu as MenuIcon,
  GitHub,
  Assignment,
  Description,
  Assessment,
  Home,
  Close as CloseIcon
} from '@mui/icons-material';
import { Link, useLocation } from 'react-router-dom';

const Navigation = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const location = useLocation();

  const navigationItems = [
    { path: '/', label: 'Home', icon: <Home /> },
    { path: '/github-audit', label: 'GitHub Audit', icon: <GitHub /> },
    { path: '/jira-compliance', label: 'JIRA Compliance', icon: <Assignment /> },
    { path: '/document-analysis', label: 'Document Analysis', icon: <Description /> },
    { path: '/compliance-report', label: 'Reports', icon: <Assessment /> }
  ];

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const isActivePath = (path) => {
    return location.pathname === path;
  };

  const drawer = (
    <Box sx={{ width: 250 }}>
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        p: 2,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white'
      }}>
        <Typography variant="h6" component="div">
          SprintoBot
        </Typography>
        <IconButton 
          color="inherit" 
          onClick={handleDrawerToggle}
          sx={{ color: 'white' }}
        >
          <CloseIcon />
        </IconButton>
      </Box>
      <Divider />
      <List>
        {navigationItems.map((item) => (
          <ListItem 
            button 
            key={item.path}
            component={Link}
            to={item.path}
            onClick={handleDrawerToggle}
            sx={{
              backgroundColor: isActivePath(item.path) ? 'rgba(102, 126, 234, 0.1)' : 'transparent',
              borderRight: isActivePath(item.path) ? '3px solid #667eea' : 'none',
              '&:hover': {
                backgroundColor: 'rgba(102, 126, 234, 0.05)'
              }
            }}
          >
            <ListItemIcon sx={{ color: isActivePath(item.path) ? '#667eea' : 'inherit' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText 
              primary={item.label}
              sx={{ color: isActivePath(item.path) ? '#667eea' : 'inherit' }}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <>
      <AppBar 
        position="sticky" 
        sx={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
        }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          
          <Typography 
            variant="h6" 
            component={Link}
            to="/"
            sx={{ 
              flexGrow: 1, 
              textDecoration: 'none', 
              color: 'inherit',
              fontWeight: 700,
              background: 'linear-gradient(45deg, #fff, #e3f2fd)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            SprintoBot
          </Typography>

          {!isMobile && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              {navigationItems.slice(1).map((item) => (
                <Button
                  key={item.path}
                  component={Link}
                  to={item.path}
                  color="inherit"
                  startIcon={item.icon}
                  sx={{
                    backgroundColor: isActivePath(item.path) ? 'rgba(255,255,255,0.1)' : 'transparent',
                    borderRadius: '25px',
                    px: 2,
                    '&:hover': {
                      backgroundColor: 'rgba(255,255,255,0.1)',
                      transform: 'translateY(-1px)'
                    },
                    transition: 'all 0.3s ease'
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {isMobile && (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: 250,
            },
          }}
        >
          {drawer}
        </Drawer>
      )}
    </>
  );
};

export default Navigation;
