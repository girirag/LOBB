import React, { useState, useEffect } from 'react';

const DEFAULT_API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [apiUrl, setApiUrl] = useState(() => {
    return localStorage.getItem('ziplink_api_url') || DEFAULT_API_URL;
  });
  const [isEditingApi, setIsEditingApi] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [activeTab, setActiveTab] = useState('shorten'); // 'shorten' | 'analytics'

  // Shorten Tab States
  const [longUrl, setLongUrl] = useState('');
  const [customCode, setCustomCode] = useState('');
  const [showCustomCode, setShowCustomCode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [shortResult, setShortResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const [history, setHistory] = useState(() => {
    try {
      const saved = localStorage.getItem('ziplink_history');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Analytics Tab States
  const [searchCode, setSearchCode] = useState('');
  const [analyticsResult, setAnalyticsResult] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsError, setAnalyticsError] = useState(null);

  // Check Backend Health
  useEffect(() => {
    checkHealth(apiUrl);
  }, [apiUrl]);

  const checkHealth = async (url) => {
    setApiStatus('checking');
    try {
      const res = await fetch(`${url.replace(/\/+$/, '')}/health`, { method: 'GET' });
      if (res.ok) {
        setApiStatus('online');
      } else {
        setApiStatus('offline');
      }
    } catch {
      setApiStatus('offline');
    }
  };

  const handleApiUrlChange = (e) => {
    const val = e.target.value.trim();
    setApiUrl(val);
    localStorage.setItem('ziplink_api_url', val);
  };

  const handleShorten = async (e) => {
    e.preventDefault();
    if (!longUrl) return;

    setError(null);
    setShortResult(null);
    setLoading(true);
    setCopied(false);

    try {
      const cleanApi = apiUrl.replace(/\/+$/, '');
      const payload = { url: longUrl };
      if (customCode.trim()) {
        payload.custom_code = customCode.trim();
      }

      const res = await fetch(`${cleanApi}/shorten`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        const msg = data.detail ? (Array.isArray(data.detail) ? data.detail[0].msg : data.detail) : 'Failed to shorten URL';
        throw new Error(msg);
      }

      setShortResult(data);
      
      // Update history in state and localStorage
      const updated = [data, ...history.filter(h => h.short_code !== data.short_code)].slice(0, 10);
      setHistory(updated);
      localStorage.setItem('ziplink_history', JSON.stringify(updated));

      setLongUrl('');
      setCustomCode('');
    } catch (err) {
      setError(err.message || 'Error connecting to backend');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFetchStats = async (codeToQuery) => {
    const code = (codeToQuery || searchCode).trim();
    if (!code) return;

    setAnalyticsError(null);
    setAnalyticsResult(null);
    setAnalyticsLoading(true);

    try {
      const cleanApi = apiUrl.replace(/\/+$/, '');
      const res = await fetch(`${cleanApi}/stats/${encodeURIComponent(code)}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Could not find link statistics');
      }

      setAnalyticsResult(data);
    } catch (err) {
      setAnalyticsError(err.message);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  return (
    <div className="container">
      {/* Top Navigation */}
      <nav className="navbar">
        <a href="/" className="logo">
          <div className="logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
            </svg>
          </div>
          <span>ZipLink</span>
        </a>

        <div className="status-badge" title={`API: ${apiUrl}`}>
          <span className={`status-dot ${apiStatus === 'offline' ? 'offline' : ''}`}></span>
          <span>
            {apiStatus === 'online' ? 'Backend Live' : apiStatus === 'checking' ? 'Connecting...' : 'Backend Offline'}
          </span>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="hero">
        <h1 className="hero-title">
          Shorten Links with <span className="gradient-text">Lightning Speed</span>
        </h1>
        <p className="hero-subtitle">
          Transform long, cumbersome URLs into clean, fast, and trackable short links.
        </p>
      </header>

      {/* Tab Switcher */}
      <div className="tabs-container">
        <button
          className={`tab-btn ${activeTab === 'shorten' ? 'active' : ''}`}
          onClick={() => setActiveTab('shorten')}
        >
          Shorten URL
        </button>
        <button
          className={`tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          Click Analytics
        </button>
      </div>

      {/* Main Content Area */}
      {activeTab === 'shorten' ? (
        <div className="glass-card">
          <form onSubmit={handleShorten}>
            <div className="form-group">
              <label className="form-label">Destination URL</label>
              <div className="input-wrapper">
                <input
                  type="url"
                  className="input-field"
                  placeholder="https://example.com/very/long/destination/url"
                  value={longUrl}
                  onChange={(e) => setLongUrl(e.target.value)}
                  required
                />
              </div>
            </div>

            <div
              className="custom-alias-toggle"
              onClick={() => setShowCustomCode(!showCustomCode)}
            >
              <span>{showCustomCode ? '▼' : '►'} Custom alias / short code (optional)</span>
            </div>

            {showCustomCode && (
              <div className="form-group" style={{ animation: 'slideUp 0.2s ease' }}>
                <label className="form-label">Custom Alias</label>
                <div className="input-wrapper">
                  <input
                    type="text"
                    className="input-field"
                    placeholder="e.g. my-promo-link"
                    value={customCode}
                    onChange={(e) => setCustomCode(e.target.value)}
                    pattern="[A-Za-z0-9_\-]{3,32}"
                    title="3-32 letters, numbers, hyphens, or underscores"
                  />
                </div>
              </div>
            )}

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? (
                <>
                  <svg width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
                    <circle cx="12" cy="12" r="10" strokeOpacity="0.25"></circle>
                    <path d="M12 2a10 10 0 0 1 10 10" strokeOpacity="0.75"></path>
                  </svg>
                  <span>Shortening URL...</span>
                </>
              ) : (
                <>
                  <span>Create Short Link</span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                  </svg>
                </>
              )}
            </button>
          </form>

          {error && (
            <div className="error-alert">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <span>{error}</span>
            </div>
          )}

          {shortResult && (
            <div className="result-card">
              <span className="result-badge">Link Created Successfully</span>
              <div className="short-url-row">
                <a
                  href={shortResult.short_url}
                  target="_blank"
                  rel="noreferrer"
                  className="short-url-text"
                >
                  {shortResult.short_url}
                </a>
                <div className="btn-group">
                  <button
                    className={`action-btn ${copied ? 'copied' : ''}`}
                    onClick={() => handleCopy(shortResult.short_url)}
                  >
                    {copied ? '✓ Copied!' : 'Copy Link'}
                  </button>
                  <a
                    href={shortResult.short_url}
                    target="_blank"
                    rel="noreferrer"
                    className="action-btn"
                  >
                    Visit ↗
                  </a>
                </div>
              </div>
              <div className="orig-url-preview">
                <strong>Original:</strong>
                <span>{shortResult.original_url}</span>
              </div>
            </div>
          )}

          {/* Recent History */}
          {history.length > 0 && (
            <div className="recent-section">
              <h3 className="section-title">Recent Links</h3>
              <div style={{ overflowX: 'auto' }}>
                <table className="url-table">
                  <thead>
                    <tr>
                      <th>Short Code</th>
                      <th>Original Destination</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((item) => (
                      <tr key={item.short_code}>
                        <td>
                          <a
                            href={item.short_url}
                            target="_blank"
                            rel="noreferrer"
                            style={{ color: '#818cf8', fontWeight: 600, textDecoration: 'none' }}
                          >
                            /{item.short_code}
                          </a>
                        </td>
                        <td style={{ color: '#94a3b8', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {item.original_url}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <button
                            className="action-btn"
                            style={{ padding: '4px 10px', fontSize: '0.78rem' }}
                            onClick={() => {
                              setActiveTab('analytics');
                              setSearchCode(item.short_code);
                              handleFetchStats(item.short_code);
                            }}
                          >
                            Stats
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Analytics Tab */
        <div className="glass-card">
          <div className="form-group">
            <label className="form-label">Enter Short Code or Alias</label>
            <div className="input-wrapper" style={{ gap: '10px' }}>
              <input
                type="text"
                className="input-field"
                placeholder="e.g. fastapi or 7xK9pq"
                value={searchCode}
                onChange={(e) => setSearchCode(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleFetchStats()}
              />
              <button
                className="action-btn"
                style={{ height: '100%', padding: '14px 24px', background: 'var(--accent-gradient)' }}
                onClick={() => handleFetchStats()}
                disabled={analyticsLoading}
              >
                {analyticsLoading ? 'Loading...' : 'Check Stats'}
              </button>
            </div>
          </div>

          {analyticsError && (
            <div className="error-alert">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <span>{analyticsError}</span>
            </div>
          )}

          {analyticsResult && (
            <div style={{ animation: 'slideUp 0.3s ease' }}>
              <div className="stats-grid">
                <div className="stat-box">
                  <div className="stat-number">{analyticsResult.clicks}</div>
                  <div className="stat-label">Total Clicks</div>
                </div>
                <div className="stat-box">
                  <div className="stat-number" style={{ fontSize: '1.2rem', marginTop: '10px' }}>
                    /{analyticsResult.short_code}
                  </div>
                  <div className="stat-label">Short Code</div>
                </div>
              </div>

              <div className="result-card" style={{ marginTop: '20px' }}>
                <div className="short-url-row">
                  <a
                    href={analyticsResult.short_url}
                    target="_blank"
                    rel="noreferrer"
                    className="short-url-text"
                  >
                    {analyticsResult.short_url}
                  </a>
                  <a
                    href={analyticsResult.short_url}
                    target="_blank"
                    rel="noreferrer"
                    className="action-btn"
                  >
                    Test Redirect ↗
                  </a>
                </div>
                <div className="orig-url-preview">
                  <strong>Target:</strong>
                  <span>{analyticsResult.original_url}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Footer & API Target Config */}
      <footer className="api-config-footer">
        <p>
          Backend API: <code style={{ color: '#818cf8' }}>{apiUrl}</code>{' '}
          <button
            style={{ background: 'none', border: 'none', color: '#6366f1', cursor: 'pointer', textDecoration: 'underline', font: 'inherit' }}
            onClick={() => setIsEditingApi(!isEditingApi)}
          >
            {isEditingApi ? 'Close' : 'Change'}
          </button>
        </p>

        {isEditingApi && (
          <div style={{ marginTop: '10px' }}>
            <input
              type="text"
              value={apiUrl}
              onChange={handleApiUrlChange}
              placeholder="https://your-backend.onrender.com"
            />
            <p style={{ fontSize: '0.75rem', marginTop: '4px', color: '#64748b' }}>
              Set this to your live Render backend URL when deployed!
            </p>
          </div>
        )}
      </footer>
    </div>
  );
}

export default App;
