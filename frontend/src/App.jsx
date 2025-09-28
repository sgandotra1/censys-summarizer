/**
 * Censys Host Summarizer - Main React Application
 * 
 * This component manages the entire frontend workflow:
 * 1. Loading host data (sample or upload)
 * 2. Host selection with checkboxes
 * 3. Sending data to backend for analysis
 * 4. Displaying colorful analysis results
 * 
 * The backend automatically switches between mock and AI modes
 * based on whether an OpenAI API key is configured.
 */

import { useState } from 'react';
import { api, ApiError } from './services/api';
import HostCard from './components/HostCard';

export default function App() {
  // State Management - All application state in one place
  const [hosts, setHosts] = useState([]);              // Array of host data objects
  const [selectedIndices, setSelectedIndices] = useState([]); // Indices of selected hosts
  const [summaries, setSummaries] = useState([]);      // Analysis results from backend
  const [loading, setLoading] = useState(false);       // Loading state during analysis
  const [error, setError] = useState('');              // Error messages for user

  /**
   * Load sample data from the server
   * 
   * Fetches /hosts_dataset.json from the public folder
   * This contains real Censys host data for demonstration
   */
  const handleLoadSample = async () => {
    try {
      setError('');  // Clear any previous errors
      console.log('📥 Loading sample Censys data...');
      
      const sampleHosts = await api.loadSampleData();
      console.log(`✅ Loaded ${sampleHosts.length} sample hosts`);
      
      setHosts(sampleHosts);
      setSelectedIndices(sampleHosts.map((_, index) => index)); // Select all hosts by default
      setSummaries([]); // Clear any previous analysis results
    } catch (err) {
      console.error('❌ Failed to load sample data:', err);
      setError(err instanceof ApiError ? err.message : 'Failed to load sample data');
    }
  };

  /**
   * Handle file upload with comprehensive validation
   * 
   * Supports multiple JSON formats:
   * - Array of hosts: [{"ip": "1.1.1.1", ...}, ...]
   * - Object with hosts: {"hosts": [{"ip": "1.1.1.1", ...}, ...]}
   */
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (file.type !== 'application/json') {
      setError('Please select a JSON file');
      return;
    }

    console.log(`📁 Reading uploaded file: ${file.name}`);

    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        setError('');
        const data = JSON.parse(e.target.result);
        
        // Handle different JSON structures
        let uploadedHosts = [];
        if (Array.isArray(data)) {
          // Direct array of hosts
          uploadedHosts = data;
          console.log(`📊 Found ${uploadedHosts.length} hosts in array format`);
        } else if (data.hosts && Array.isArray(data.hosts)) {
          // Object with "hosts" property (like Censys format)
          uploadedHosts = data.hosts;
          console.log(`📊 Found ${uploadedHosts.length} hosts in object format`);
        } else {
          setError('Invalid JSON format. Expected array of hosts or object with "hosts" property');
          return;
        }
        
        if (uploadedHosts.length === 0) {
          setError('No hosts found in file');
          return;
        }
        
        // Update application state
        setHosts(uploadedHosts);
        setSelectedIndices(uploadedHosts.map((_, index) => index)); // Select all by default
        setSummaries([]); // Clear any previous results
        
        console.log(`✅ Successfully loaded ${uploadedHosts.length} hosts from file`);
      } catch (err) {
        console.error('❌ JSON parsing error:', err);
        setError('Invalid JSON file format');
      }
    };
    
    reader.onerror = () => {
      console.error('❌ File reading error');
      setError('Failed to read file');
    };
    
    reader.readAsText(file);
  };

  /**
   * Toggle host selection using index-based approach
   * 
   * Uses indices instead of object comparison to avoid React state issues
   * This ensures the UI updates properly when hosts are selected/deselected
   */
  const handleHostToggle = (hostIndex) => {
    console.log(`🔄 Toggling selection for host at index ${hostIndex}`);
    
    if (selectedIndices.includes(hostIndex)) {
      // Remove this host from selection
      const newSelection = selectedIndices.filter(idx => idx !== hostIndex);
      setSelectedIndices(newSelection);
      console.log(`➖ Deselected host ${hostIndex}, now ${newSelection.length} selected`);
    } else {
      // Add this host to selection
      const newSelection = [...selectedIndices, hostIndex];
      setSelectedIndices(newSelection);
      console.log(`➕ Selected host ${hostIndex}, now ${newSelection.length} selected`);
    }
  };

  /**
   * Send selected hosts to backend for analysis
   * 
   * This triggers either:
   * - Mock analysis (rule-based, no API key needed)
   * - Real AI analysis (if OpenAI API key is configured)
   */
  const handleSummarize = async () => {
    // Get actual host objects from selected indices
    const selectedHosts = selectedIndices.map(index => hosts[index]);
    
    if (selectedHosts.length === 0) {
      setError('Select at least one host to analyze');
      return;
    }

    console.log(`🚀 Starting analysis of ${selectedHosts.length} hosts...`);
    console.log(`📋 Selected hosts: ${selectedHosts.map(h => getHostId(h)).join(', ')}`);

    setLoading(true);  // Show loading state in UI
    setError('');      // Clear any previous errors
    
    try {
      // Send to backend API
      const result = await api.summarizeHosts(selectedHosts);
      const summaries = result.items || [];
      
      console.log(`✅ Analysis complete: ${summaries.length} summaries received`);
      setSummaries(summaries);
      
      // Handle edge case where no summaries were generated
      if (summaries.length === 0) {
        setError('No summaries were generated. Please check backend logs for details.');
      } else if (summaries.length < selectedHosts.length) {
        console.log(`⚠️  Only ${summaries.length}/${selectedHosts.length} hosts were successfully analyzed`);
      }
    } catch (err) {
      console.error('❌ Analysis failed:', err);
      const errorMessage = err instanceof ApiError ? err.message : 'Analysis failed';
      setError(`${errorMessage}. Please ensure the backend is running on http://localhost:8000`);
    } finally {
      setLoading(false);  // Hide loading state
    }
  };

  /**
   * Clear analysis results and allow new analysis
   * 
   * This resets the results view while keeping host selection intact
   */
  const handleClearResults = () => {
    console.log('🧹 Clearing analysis results');
    setSummaries([]);
  };

  /**
   * Extract host identifier from host data
   * 
   * Handles different naming conventions in host data
   */
  const getHostId = (host) => {
    return host.ip || host.host || host.hostname || 'Unknown';
  };

  /**
   * Get service count for display in host list
   * 
   * Handles both Censys format (services array) and simple format (ports array)
   */
  const getServiceCount = (host) => {
    if (host.services && Array.isArray(host.services)) {
      return `${host.services.length} services`;  // Censys format
    } else if (host.ports && host.ports.length > 0) {
      return `${host.ports.length} ports`;        // Simple format
    }
    return null;  // No service information available
  };

  // Main UI Render
  return (
    <div className="container">
      {/* Application Header */}
      <div className="header">
        <div className="header-icon">
          {/* Security shield icon */}
          <svg width="32" height="32" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: 'white' }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <h1 className="header-title">Censys Host Summarizer</h1>
        <p className="header-subtitle">AI-powered network host security analysis</p>
      </div>

      {/* Data Loading Controls */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '2rem' }}>
        {/* Load sample data button */}
        <button onClick={handleLoadSample} className="btn btn-primary">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Load sample
        </button>
        
        {/* File upload button */}
        <label className="btn btn-secondary">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Upload JSON
          <input
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </label>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-card">
          <svg className="error-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="error-text">{error}</p>
          <button onClick={() => setError('')} className="error-close">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Main Content Layout */}
      <div className="main-layout">
        {/* Left Sidebar - Host Selection */}
        {hosts.length > 0 && (
          <div className="sidebar">
            <div className="host-selection">
              <h2 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', marginBottom: '1rem' }}>
                Select hosts ({selectedIndices.length} of {hosts.length} selected)
              </h2>
              
              {/* Scrollable host list with checkboxes */}
              <div style={{ maxHeight: '300px', overflowY: 'auto', marginBottom: '1.5rem' }}>
                {hosts.map((host, index) => {
                  const isSelected = selectedIndices.includes(index);
                  const hostId = getHostId(host);
                  const serviceCount = getServiceCount(host);
                  
                  return (
                    <label key={index} className="host-item">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleHostToggle(index)}
                        className="host-checkbox"
                      />
                      <div className="host-info">
                        <div className="host-name">{hostId}</div>
                        {/* Show service/port count if available */}
                        {serviceCount && <div className="host-meta">{serviceCount}</div>}
                      </div>
                    </label>
                  );
                })}
              </div>
              
              {/* Action buttons in sidebar (moved here for better UX) */}
              {selectedIndices.length > 0 && (
                <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '1rem' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {/* Main analyze button */}
                    <button
                      onClick={handleSummarize}
                      disabled={loading}
                      className="btn btn-analyze"
                      style={{ width: '100%', justifyContent: 'center' }}
                    >
                      {loading ? (
                        <span style={{ display: 'flex', alignItems: 'center' }}>
                          <div className="spinner" style={{ marginRight: '8px' }}></div>
                          Analyzing...
                        </span>
                      ) : (
                        `Summarize ${selectedIndices.length} Host${selectedIndices.length !== 1 ? 's' : ''}`
                      )}
                    </button>
                    
                    {/* Clear results button (only shows after analysis) */}
                    {summaries.length > 0 && (
                      <button
                        onClick={handleClearResults}
                        className="btn btn-clear"
                        style={{ width: '100%', justifyContent: 'center' }}
                      >
                        Clear Results
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Right Content Area - Analysis Results */}
        {summaries.length > 0 && (
          <div className="content">
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem' }}>
              Analysis Results ({summaries.length})
            </h2>
            
            {/* Render each host analysis as a card */}
            {summaries.map((summary, index) => (
              <HostCard 
                key={`${summary.host_id}-${index}`} 
                host={summary} 
              />
            ))}
          </div>
        )}
      </div>

      {/* Empty State - Shows when no hosts are loaded */}
      {hosts.length === 0 && (
        <div className="empty-state">
          <svg className="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="empty-title">No hosts loaded</h3>
          <p className="empty-text">Upload a JSON file or load sample data to get started</p>
        </div>
      )}
    </div>
  );
}