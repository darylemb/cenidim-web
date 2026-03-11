import React, { useState, useEffect } from 'react';

// Modal component to show lyrics
const LyricModal = ({ songId, onClose }) => {
  const [song, setSong] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch full song details including lyrics
    fetch(`/api/song/${songId}`)
      .then(res => res.json())
      .then(data => {
        setSong(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching song details:", err);
        setLoading(false);
      });
  }, [songId]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>{song ? song.title : 'Cargando...'}</h3>
            <span className="album-info">{song ? song.album : ''}</span>
          </div>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          {loading ? (
            <p>Obteniendo letra...</p>
          ) : song && song.lyrics ? (
            song.lyrics
          ) : (
            <p>No se encontró la letra de esta canción.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export const Buscador = () => {
  const [query, setQuery] = useState('');
  const [field, setField] = useState('all');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedSongId, setSelectedSongId] = useState(null);

  // Perform search on mount (empty query returns default data) and when submit button clicked
  const handleSearch = () => {
    setLoading(true);
    // API endpoint is proxied via package.json to localhost:8000
    fetch(`/api/search?query=${encodeURIComponent(query)}&field=${field}`)
      .then(res => res.json())
      .then(data => {
        setResults(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error searching:", err);
        setLoading(false);
      });
  };

  // Run initial default search
  useEffect(() => {
    handleSearch();
  }, []);

  const handleReset = () => {
    setQuery('');
    setField('all');
    // Fetch all default after state updates
    setTimeout(() => {
      fetch(`/api/search?query=&field=all`)
        .then(res => res.json())
        .then(data => setResults(data));
    }, 50);
  };

  return (
    <div className="content-area">
      <h2 className="page-title">Buscador</h2>
      
      <div className="search-container">
        <button className="btn-reset" onClick={handleReset}>
          Reset
        </button>
        
        <select 
          value={field} 
          onChange={(e) => setField(e.target.value)}
        >
          <option value="all">Filtro General</option>
          <option value="album">Álbum</option>
          <option value="title">Título</option>
          <option value="lyrics">Contenido (Letra)</option>
        </select>
        
        <input 
          type="text" 
          placeholder="Buscar..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        
        <button className="action-btn" onClick={handleSearch}>
          Buscar
        </button>
      </div>

      {loading ? (
        <p>Buscando en la base de datos...</p>
      ) : (
        <table className="results-table">
          <thead>
            <tr>
              <th>Álbum</th>
              <th>Título</th>
              <th>Archivo Original</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            {results.length > 0 ? results.map(song => (
              <tr key={song.id}>
                <td>{song.album}</td>
                <td>{song.title}</td>
                <td>{song.filename}</td>
                <td>
                  <button 
                    className="action-btn"
                    onClick={() => setSelectedSongId(song.id)}
                  >
                    Ver Letra
                  </button>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan="4" style={{textAlign: 'center', padding: '2rem'}}>
                  No se encontraron resultados para su búsqueda.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {/* Render modal if a song is selected */}
      {selectedSongId && (
        <LyricModal 
          songId={selectedSongId} 
          onClose={() => setSelectedSongId(null)} 
        />
      )}
    </div>
  );
};
