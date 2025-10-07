import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class EvidenceService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`Making request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(this.handleError(error));
      }
    );
  }

  handleError(error) {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'Server error';
      return new Error(`${error.response.status}: ${message}`);
    } else if (error.request) {
      // Request made but no response received
      return new Error('No response from server. Please check your connection.');
    } else {
      // Something else happened
      return new Error(error.message || 'An unexpected error occurred');
    }
  }

  async submitQuery(query, queryType = null, filters = {}) {
    try {
      const payload = {
        query,
        query_type: queryType,
        filters: Object.keys(filters).length > 0 ? filters : null,
      };

      const response = await this.client.post('/evidence/query', payload);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async submitDocumentQuery(query, filters = {}) {
    try {
      const payload = {
        query,
        filters: Object.keys(filters).length > 0 ? filters : null,
      };

      const response = await this.client.post('/evidence/documents/query', payload);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async getEvidence(queryId) {
    try {
      const response = await this.client.get(`/evidence/evidence/${queryId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async exportEvidence(queryId, format = 'json') {
    try {
      const response = await this.client.post(`/evidence/export/${queryId}`, {
        query_id: queryId,
        format: format,
        include_metadata: true,
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async uploadDocument(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await this.client.post('/evidence/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async healthCheck() {
    try {
      const response = await this.client.get('/evidence/health');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // GitHub-specific queries
  async queryGitHub(repo, prNumber = null, searchParams = {}) {
    const query = prNumber 
      ? `Why was PR #${prNumber} in ${repo} merged?`
      : `Show me pull requests in ${repo}`;
    
    return this.submitQuery(query, 'github', { repo, pr_number: prNumber, ...searchParams });
  }

  // JIRA-specific queries
  async queryJIRA(ticketKey = null, searchParams = {}) {
    const query = ticketKey
      ? `Show me details for ticket ${ticketKey}`
      : 'Show me JIRA tickets';
    
    return this.submitQuery(query, 'jira', { ticket_key: ticketKey, ...searchParams });
  }

  // Document-specific queries
  async queryDocuments(searchTerms, documentType = null) {
    try {
      const response = await this.client.post('/evidence/documents/query', {
        query: searchTerms,
        filters: documentType ? { document_type: documentType } : {}
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Reports functionality
  async getReports() {
    try {
      const response = await this.client.get('/evidence/reports');
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  async exportReport(reportId, format = 'pdf') {
    try {
      const response = await this.client.post(`/evidence/reports/${reportId}/export`, null, {
        params: { format },
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }
}

export const evidenceService = new EvidenceService();
export default EvidenceService;
