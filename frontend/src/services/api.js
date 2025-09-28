/**
 * API Service - Handles all communication with the backend
 * 
 * This service provides a clean interface for:
 * 1. Loading sample data from the frontend
 * 2. Sending host data to backend for analysis
 * 3. Checking backend health status
 * 
 * The backend automatically chooses between mock and AI analysis
 * based on whether an OpenAI API key is configured.
 */

// Backend URL - can be overridden with environment variable
const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

/**
 * Custom error class for API-related errors
 * 
 * Provides structured error information including HTTP status codes
 */
export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
  
  /**
   * Check if this is a network connectivity error
   */
  get isNetworkError() {
    return this.status === 0;
  }
  
  /**
   * Check if this is a client error (4xx)
   */
  get isClientError() {
    return this.status >= 400 && this.status < 500;
  }
  
  /**
   * Check if this is a server error (5xx)
   */
  get isServerError() {
    return this.status >= 500;
  }
}

/**
 * Make HTTP request with comprehensive error handling
 * 
 * Handles network errors, HTTP errors, and JSON parsing errors
 * Returns parsed JSON response or throws ApiError
 */
async function makeRequest(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`;
  console.log(`🌐 API Request: ${options.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    console.log(`📡 Response: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      // Try to get error details from response
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    const data = await response.json();
    console.log(`✅ Success: Received ${JSON.stringify(data).length} bytes`);
    return data;
    
  } catch (error) {
    if (error instanceof ApiError) throw error;
    
    // Network or other errors
    console.error('❌ Network error:', error);
    throw new ApiError(`Network error: ${error.message}`);
  }
}

/**
 * API service methods
 */
export const api = {
  /**
   * Check backend health status
   * 
   * Returns: {"ok": true} if backend is running
   * Used to verify connectivity before making analysis requests
   */
  async checkHealth() {
    console.log('🏥 Checking backend health...');
    return makeRequest('/health');
  },

  /**
   * Load sample host data from frontend public folder
   * 
   * The sample data contains real Censys host information
   * Handles different JSON formats automatically:
   * - Direct array: [{"ip": "1.1.1.1", ...}, ...]
   * - Wrapped object: {"hosts": [{"ip": "1.1.1.1", ...}, ...]}
   */
  async loadSampleData() {
    console.log('📂 Loading sample host data...');
    
    try {
      const response = await fetch('/hosts_dataset.json');
      if (!response.ok) {
        throw new ApiError(`Failed to load sample data: ${response.status}`, response.status);
      }
      
      const data = await response.json();
      console.log('📊 Sample data loaded, parsing format...');
      
      // Handle different JSON structures
      if (Array.isArray(data)) {
        console.log(`✅ Found ${data.length} hosts in array format`);
        return data;
      } else if (data.hosts && Array.isArray(data.hosts)) {
        console.log(`✅ Found ${data.hosts.length} hosts in object format`);
        return data.hosts;
      } else {
        throw new ApiError('Sample data format not recognized - expected array or object with hosts property');
      }
    } catch (error) {
      if (error instanceof ApiError) throw error;
      console.error('❌ Sample data loading error:', error);
      throw new ApiError(`Failed to load sample data: ${error.message}`);
    }
  },

  /**
   * Send hosts to backend for AI/mock analysis
   * 
   * This is where the magic happens:
   * - Sends real host data to backend
   * - Backend decides between mock or AI analysis
   * - Returns structured security analysis
   * 
   * The analysis quality depends on backend mode:
   * - Mock mode: Rule-based pattern matching
   * - AI mode: Real OpenAI GPT analysis (requires API key)
   */
  async summarizeHosts(hosts) {
    if (!Array.isArray(hosts) || hosts.length === 0) {
      throw new ApiError('No hosts provided for analysis');
    }

    console.log(`🔍 Sending ${hosts.length} hosts for analysis...`);
    console.log(`📋 Host IPs: ${hosts.map(h => h.ip || h.host || 'unknown').join(', ')}`);

    const startTime = Date.now();
    
    try {
      const result = await makeRequest('/summarize', {
        method: 'POST',
        body: JSON.stringify({ hosts }),
      });
      
      const duration = Date.now() - startTime;
      console.log(`⏱️  Analysis completed in ${duration}ms`);
      console.log(`📊 Results: ${result.items?.length || 0} summaries generated`);
      
      return result;
    } catch (error) {
      console.error('❌ Analysis request failed:', error);
      throw error;
    }
  }
};