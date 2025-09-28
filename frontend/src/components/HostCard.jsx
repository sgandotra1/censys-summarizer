/**
 * HostCard Component - Displays detailed security analysis for a single host
 * 
 * This component renders:
 * - Host header with IP and overview
 * - Key services as colorful chips
 * - Security risks with color-coded severity badges
 * - Security recommendations with green styling
 * - JSON export functionality
 * 
 * The data displayed here comes from either:
 * - Mock analysis (rule-based, no API key)
 * - Real AI analysis (OpenAI GPT, requires API key)
 */

import { useState } from 'react';

/**
 * Severity Badge Component
 * 
 * Displays risk severity levels with distinct colors:
 * - CRITICAL: Red (immediate action required)
 * - HIGH: Orange (urgent attention needed)
 * - MEDIUM: Yellow (should be addressed)
 * - LOW: Green (monitor and plan)
 */
function SeverityBadge({ severity }) {
  // Map severity levels to CSS classes (defined in index.css)
  const severityClass = `severity-${severity.toLowerCase()}`;
  
  return (
    <span className={`severity-badge ${severityClass}`}>
      {severity.toUpperCase()}
    </span>
  );
}

/**
 * Service Chip Component
 * 
 * Displays individual services as styled chips
 * Shows port number and service name (e.g., "80: HTTP", "22: SSH")
 */
function ServiceChip({ service }) {
  return (
    <span className="service-chip">
      {service.port && `${service.port}: `}{service.name}
    </span>
  );
}

/**
 * Main HostCard Component
 * 
 * Props:
 * - host: HostSummary object containing analysis results
 */
export default function HostCard({ host }) {
  // State for JSON modal visibility
  const [showJson, setShowJson] = useState(false);
  // State for copy button feedback
  const [copyStatus, setCopyStatus] = useState('');

  /**
   * Copy host data to clipboard with fallback support
   * 
   * Tries modern clipboard API first, falls back to legacy method
   * Provides visual feedback to user about copy success/failure
   */
  const copyToClipboard = async () => {
    try {
      // Prepare JSON data for copying
      const jsonText = JSON.stringify(host, null, 2);
      
      // Try modern clipboard API (works in most browsers)
      await navigator.clipboard.writeText(jsonText);
      console.log('✅ Copied to clipboard using modern API');
      setCopyStatus('Copied!');
      setTimeout(() => setCopyStatus(''), 2000);  // Reset after 2 seconds
      
    } catch (err) {
      console.warn('⚠️  Modern clipboard API failed, trying fallback:', err);
      
      // Fallback method for older browsers
      try {
        const textArea = document.createElement('textarea');
        textArea.value = JSON.stringify(host, null, 2);
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');  // Legacy copy method
        document.body.removeChild(textArea);
        
        console.log('✅ Copied to clipboard using fallback method');
        setCopyStatus('Copied!');
        setTimeout(() => setCopyStatus(''), 2000);
      } catch (fallbackErr) {
        console.error('❌ All copy methods failed:', fallbackErr);
        setCopyStatus('Copy failed');
        setTimeout(() => setCopyStatus(''), 2000);
      }
    }
  };

  return (
    <>
      {/* Main host card with gradient background and hover effects */}
      <div className="host-card">
        
        {/* Header Section - Host ID and overview */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
          <div style={{ flex: 1 }}>
            <div className="host-header">
              <h3 className="host-title">{host.host_id}</h3>
              <div className="host-indicator"></div> {/* Blue gradient dot */}
            </div>
            <p className="host-overview">{host.overview}</p>
          </div>
          
          {/* JSON export button */}
          <button
            onClick={() => setShowJson(true)}
            style={{
              background: 'none',
              border: 'none',
              padding: '8px',
              borderRadius: '8px',
              color: '#9ca3af',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={(e) => {
              e.target.style.background = '#eff6ff';
              e.target.style.color = '#3b82f6';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'none';
              e.target.style.color = '#9ca3af';
            }}
            title="View JSON"
          >
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </button>
        </div>

        {/* Key Services Section */}
        {host.key_services?.length > 0 && (
          <div style={{ marginBottom: '1.5rem' }}>
            <div className="section-header">
              <div className="section-indicator services"></div> {/* Blue gradient indicator */}
              <h4 className="section-title">Key Services</h4>
            </div>
            {/* Service chips in flexible layout */}
            <div className="services-container">
              {host.key_services.map((service, index) => (
                <ServiceChip key={index} service={service} />
              ))}
            </div>
          </div>
        )}

        {/* Security Risks Section */}
        {host.risks?.length > 0 && (
          <div className="risks-container">
            <div className="section-header">
              <div className="section-indicator risks"></div> {/* Red-orange gradient indicator */}
              <h4 className="section-title">Security Risks</h4>
            </div>
            {/* Individual risk items with severity badges */}
            <div>
              {host.risks.map((risk, index) => (
                <div key={index} className="risk-item">
                  <SeverityBadge severity={risk.severity} />
                  <div className="risk-content">
                    <div className="risk-title">{risk.risk}</div>
                    {/* Show evidence if available */}
                    {risk.evidence && (
                      <div className="risk-evidence">{risk.evidence}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations Section */}
        {host.recommendations?.length > 0 && (
          <div className="recommendations-container">
            <div className="section-header">
              <div className="section-indicator recommendations"></div> {/* Green gradient indicator */}
              <h4 className="section-title">Recommendations</h4>
            </div>
            {/* Recommendation items with green styling */}
            <div>
              {host.recommendations.map((rec, index) => (
                <div key={index} className="recommendation-item">
                  <div className="recommendation-dot"></div> {/* Green gradient dot */}
                  <div className="recommendation-text">{rec}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* JSON Export Modal */}
      {showJson && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1rem',
            zIndex: 1000
          }}
          onClick={() => setShowJson(false)}
        >
          <div 
            style={{
              background: 'white',
              borderRadius: '16px',
              boxShadow: '0 25px 50px rgba(0, 0, 0, 0.3)',
              maxWidth: '600px',
              width: '100%',
              maxHeight: '80vh',
              display: 'flex',
              flexDirection: 'column'
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Modal header */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              padding: '1.5rem',
              borderBottom: '1px solid #e5e7eb'
            }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600' }}>Host Summary JSON</h3>
              <div style={{ display: 'flex', gap: '8px' }}>
                {/* Copy button with status feedback */}
                <button
                  onClick={copyToClipboard}
                  className="btn btn-primary"
                  style={{ 
                    // Dynamic styling based on copy status
                    background: copyStatus === 'Copied!' ? 'linear-gradient(135deg, #10b981, #059669)' : 
                                copyStatus === 'Copy failed' ? 'linear-gradient(135deg, #ef4444, #dc2626)' : 
                                'linear-gradient(135deg, #3b82f6, #6366f1)'
                  }}
                >
                  {copyStatus || 'Copy'}
                </button>
                
                {/* Close modal button */}
                <button
                  onClick={() => setShowJson(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: '8px',
                    borderRadius: '8px',
                    color: '#9ca3af',
                    cursor: 'pointer'
                  }}
                >
                  <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            {/* JSON content display */}
            <div style={{ flex: 1, overflow: 'auto', padding: '1.5rem' }}>
              <pre style={{ 
                fontSize: '12px', 
                color: '#374151', 
                whiteSpace: 'pre-wrap', 
                fontFamily: 'monospace',
                background: '#f8fafc',
                padding: '1rem',
                borderRadius: '8px',
                border: '1px solid #e2e8f0'
              }}>
                {JSON.stringify(host, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </>
  );
}