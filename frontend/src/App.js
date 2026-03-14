import React, { useState, useEffect, useCallback } from 'react';
import './index.css';
import { CombinedHeader } from './components/CombinedHeader';
import { Canciones } from './components/Canciones';
import { DashboardView } from './components/DashboardView';
import { apiService } from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState("Canciones");

  // Search state lifted from Canciones.jsx
  const [query, setQuery] = useState('');
  const [field, setField] = useState('all');
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [loading, setLoading] = useState(false);

  // Perform search (params-driven to be stable)
  const performSearch = useCallback((searchTerm, searchField, targetPage = 1, targetLimit = 20) => {
    setLoading(true);
    // Update local state to reflect the search parameters being used
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

  return (
    <div className="app-container">
      <CombinedHeader
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        query={query}
        setQuery={setQuery}
        field={field}
        setField={setField}
        performSearch={performSearch}
        handleReset={handleReset}
        page={page}
        limit={limit}
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
