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
  const [loading, setLoading] = useState(false);

  // Perform search (params-driven to be stable)
  const performSearch = useCallback((searchTerm, searchField) => {
    setLoading(true);
    apiService
      .searchSongs(searchTerm, searchField)
      .then((data) => {
        setResults(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  // Run initial default search on mount
  useEffect(() => {
    performSearch('', 'all');
  }, [performSearch]);

  const handleReset = () => {
    setQuery('');
    setField('all');
    performSearch('', 'all');
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
      />

      <main>
        {activeTab === "Canciones" ? (
          <Canciones
            results={results}
            loading={loading}
            handleReset={handleReset}
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
