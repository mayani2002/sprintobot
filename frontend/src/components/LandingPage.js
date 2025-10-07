import React from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';

const LandingPage = () => {
  const useCases = [
    {
      id: 'github-audit',
      title: 'GitHub Audit',
      description: 'Analyze pull requests, code reviews, and repository compliance',
      icon: '🔍',
      features: ['PR approval status', 'Code review compliance', 'Branch protection rules'],
      path: '/github-audit'
    },
    {
      id: 'jira-compliance',
      title: 'JIRA Compliance',
      description: 'Track ticket workflows, approvals, and process adherence',
      icon: '📋',
      features: ['Workflow compliance', 'Approval tracking', 'SLA monitoring'],
      path: '/jira-compliance'
    },
    {
      id: 'document-analysis',
      title: 'Document Analysis',
      description: 'Parse and analyze PDF, Excel, and CSV files for evidence',
      icon: '📄',
      features: ['PDF parsing', 'Excel analysis', 'CSV processing'],
      path: '/document-analysis'
    },
    {
      id: 'incident-investigation',
      title: 'Incident Investigation',
      description: 'Gather evidence across multiple systems for incident response',
      icon: '🚨',
      features: ['Multi-source evidence', 'Timeline reconstruction', 'Impact analysis'],
      path: '/incident-investigation'
    },
    {
      id: 'compliance-report',
      title: 'Compliance Reporting',
      description: 'Generate comprehensive compliance reports and evidence packages',
      icon: '📊',
      features: ['Automated reports', 'Evidence packaging', 'Export capabilities'],
      path: '/compliance-report'
    },
    {
      id: 'ai-query',
      title: 'AI Query Assistant',
      description: 'Natural language queries for evidence discovery and analysis',
      icon: '🤖',
      features: ['Natural language processing', 'Smart evidence discovery', 'Contextual analysis'],
      path: '/ai-query'
    }
  ];

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">
            <span className="gradient-text">SprintoBot</span>
            <br />
            AI-Powered Evidence on Demand
          </h1>
          <p className="hero-subtitle">
            Instantly fetch and format required evidence from various systems during audits, 
            compliance checks, or incident investigations using natural language queries.
          </p>
          <div className="hero-stats">
            <div className="stat">
              <span className="stat-number">50%</span>
              <span className="stat-label">Faster Evidence Collection</span>
            </div>
            <div className="stat">
              <span className="stat-number">90%</span>
              <span className="stat-label">Accuracy Improvement</span>
            </div>
            <div className="stat">
              <span className="stat-number">24/7</span>
              <span className="stat-label">Availability</span>
            </div>
          </div>
        </div>
      </section>

      {/* Platform Overview */}
      <section className="platform-overview">
        <div className="container">
          <h2>How SprintoBot Works</h2>
          <div className="process-steps">
            <div className="step">
              <div className="step-icon">🎯</div>
              <h3>Query</h3>
              <p>Ask questions in natural language about compliance, audits, or incidents</p>
            </div>
            <div className="step">
              <div className="step-icon">🔍</div>
              <h3>Discover</h3>
              <p>AI automatically identifies and retrieves relevant evidence from multiple sources</p>
            </div>
            <div className="step">
              <div className="step-icon">📋</div>
              <h3>Format</h3>
              <p>Evidence is formatted and organized for auditor review and compliance reporting</p>
            </div>
            <div className="step">
              <div className="step-icon">📤</div>
              <h3>Export</h3>
              <p>Generate reports in CSV, Excel, or PDF format for stakeholders</p>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases Grid */}
      <section className="use-cases">
        <div className="container">
          <h2>Choose Your Use Case</h2>
          <p className="section-subtitle">
            Select the type of evidence collection and analysis you need
          </p>
          <div className="use-cases-grid">
            {useCases.map((useCase) => (
              <Link key={useCase.id} to={useCase.path} className="use-case-card">
                <div className="use-case-icon">{useCase.icon}</div>
                <h3>{useCase.title}</h3>
                <p>{useCase.description}</p>
                <ul className="features-list">
                  {useCase.features.map((feature, index) => (
                    <li key={index}>✓ {feature}</li>
                  ))}
                </ul>
                <div className="card-footer">
                  <span className="cta-text">Get Started →</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="container">
          <h2>Platform Features</h2>
          <div className="features-grid">
            <div className="feature">
              <div className="feature-icon">🔗</div>
              <h3>Multi-System Integration</h3>
              <p>Connect to GitHub, JIRA, and other enterprise systems seamlessly</p>
            </div>
            <div className="feature">
              <div className="feature-icon">🤖</div>
              <h3>AI-Powered Analysis</h3>
              <p>Natural language processing with OpenAI and LangChain for intelligent queries</p>
            </div>
            <div className="feature">
              <div className="feature-icon">📊</div>
              <h3>Comprehensive Reporting</h3>
              <p>Generate detailed reports with evidence trails and compliance metrics</p>
            </div>
            <div className="feature">
              <div className="feature-icon">🔒</div>
              <h3>Enterprise Security</h3>
              <p>Role-based access control and audit trails for enterprise compliance</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta">
        <div className="container">
          <h2>Ready to Transform Your Audit Process?</h2>
          <p>Start collecting evidence faster and more accurately with AI assistance</p>
          <Link to="/ai-query" className="cta-button">
            Start with AI Query Assistant
          </Link>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
