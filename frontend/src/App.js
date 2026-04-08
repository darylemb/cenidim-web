import React, { useState, useEffect, useCallback } from 'react';
import './index.css';
import { CombinedHeader } from './components/CombinedHeader';
import { Canciones } from './components/Canciones';
import { DashboardView } from './components/DashboardView';
import { Timeline } from './components/Timeline';
import { AuthPage } from './components/AuthPage';
import { AdminPanel } from './components/AdminPanel';
import { apiService } from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState("Línea de tiempo");

  // Auth state
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [showAuth, setShowAuth] = useState(false);

  // Search state lifted from Canciones.jsx
  const [query, setQuery] = useState('');
  const [field, setField] = useState('all');
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [loading, setLoading] = useState(false);

  // Restore session on mount
  useEffect(() => {
    const token = localStorage.getItem('cenidim_token');
    if (token) {
      apiService.getMe().then((u) => {
        if (u) setUser(u);
        else localStorage.removeItem('cenidim_token');
        setAuthLoading(false);
      });
    } else {
      setAuthLoading(false);
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setShowAuth(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('cenidim_token');
    setUser(null);
    if (activeTab === 'Admin') setActiveTab('Línea de tiempo');
  };

  // Block navigation to Admin when not logged in
  const handleSetActiveTab = (tab) => {
    if (tab === 'Admin' && !user) {
      setShowAuth(true);
      return;
    }
    setActiveTab(tab);
  };

  // Perform search (params-driven to be stable)
  const performSearch = useCallback((searchTerm, searchField, targetPage = 1, targetLimit = 20) => {
    setLoading(true);
    setPage(targetPage);
    setLimit(targetLimit);
    
    apiService
      .searchSongs(searchTerm, searchField, targetPage, targetLimit)
      .then((data) => {
        setResults(data.results || []);
        setTotal(data.total || 0);
        setLoading(false);
      })
      .catch(() => {
        setResults([]);
        setTotal(0);
        setLoading(false);
      });
  }, []);

  // Run initial default search on mount
  useEffect(() => {
    performSearch('', 'all', 1, 20);
  }, [performSearch]);

  const handleReset = () => {
    setQuery('');
    setField('all');
    performSearch('', 'all', 1, 20);
  };

  if (authLoading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Cargando...</div>;
  }

  if (showAuth) {
    return (
      <div className="app-container">
        <AuthPage onLogin={handleLogin} />
      </div>
    );
  }

  return (
    <div className="app-container">
      <CombinedHeader
        activeTab={activeTab}
        setActiveTab={handleSetActiveTab}
        query={query}
        setQuery={setQuery}
        field={field}
        setField={setField}
        performSearch={performSearch}
        handleReset={handleReset}
        limit={limit}
        user={user}
        onLogout={handleLogout}
        onLoginClick={() => setShowAuth(true)}
      />

      <main>
        {activeTab === "Canciones" ? (
          <Canciones
            results={results}
            total={total}
            page={page}
            limit={limit}
            loading={loading}
            handleReset={handleReset}
            performSearch={performSearch}
            query={query}
            field={field}
          />
        ) : activeTab === "Dashboards" ? (
          <DashboardView />
        ) : activeTab === "Línea de tiempo" ? (
          <Timeline />
        ) : activeTab === "Admin" && user ? (
          <AdminPanel user={user} />
        ) : (
          <div className="content-area">
            <h2 className="page-title">{activeTab}</h2>
            <p>Sección en construcción. Por favor visite la sección del <strong>Canciones</strong> o <strong>Dashboards</strong>.</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

