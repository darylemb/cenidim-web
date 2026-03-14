import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

// Modal component to show lyrics
const LyricModal = ({ songId, onClose }) => {
  const [song, setSong] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch full song details including lyrics
    apiService
      .getSongDetail(songId)
      .then((data) => {
        setSong(data);
        setLoading(false);
      })
      .catch(() => {
        // Error logging is already handled in the service
        setLoading(false);
      });
  }, [songId]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lyric-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <h3 id="lyric-modal-title">{song ? song.title : 'Cargando...'}</h3>
            <span className="album-info">{song ? song.album : ''}</span>
          </div>
          <button className="close-btn" onClick={onClose} aria-label="Cerrar">
            &times;
          </button>
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

export const Canciones = ({
  results = [],
  total = 0,
  page = 1,
  limit = 20,
  loading = false,
  handleReset,
  performSearch,
  query,
  field,
}) => {
  const [selectedSongId, setSelectedSongId] = useState(null);

  const totalPages = Math.ceil(total / limit);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      performSearch(query, field, newPage, limit);
      const prefersReducedMotion =
        typeof window !== 'undefined' &&
        typeof window.matchMedia === 'function' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      if (prefersReducedMotion) {
        window.scrollTo(0, 0);
      } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
  };

  const handleLimitChange = (e) => {
    const newLimit = parseInt(e.target.value, 10);
    performSearch(query, field, 1, newLimit);
  };

  return (
    <div className="content-area">
      <div className="page-header-flex">
        <h2 className="page-title">Canciones</h2>
        <div className="total-indicator">
          <strong>{total}</strong> canciones encontradas
        </div>
      </div>

      <div className="results-table-container">
        {loading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
            <p>Buscando en el archivo del CENIDIM...</p>
          </div>
        )}
        <table className={`results-table ${loading ? 'loading-opacity' : ''}`}>
          <thead>
            <tr>
              <th>Álbum</th>
              <th>Título</th>
              <th>Archivo</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            {!loading && results.length > 0 ? (
              results.map((song) => (
                <tr key={song.id}>
                  <td data-label="Álbum">{song.album}</td>
                  <td data-label="Título">{song.title}</td>
                  <td data-label="Archivo">{song.filename}</td>
                  <td data-label="Acción">
                    <button className="action-btn" onClick={() => setSelectedSongId(song.id)}>
                      Ver Letra
                    </button>
                  </td>
                </tr>
              ))
            ) : !loading ? (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '4rem' }}>
                  <div className="no-results">
                    <span style={{ fontSize: '2rem', display: 'block', marginBottom: '1rem' }}>
                      🔍
                    </span>
                    <p>No se encontraron resultados para su búsqueda.</p>
                    <button
                      className="btn-reset"
                      style={{ marginTop: '1rem' }}
                      onClick={handleReset}
                    >
                      Mostrar todas las canciones
                    </button>
                  </div>
                </td>
              </tr>
            ) : (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '2rem' }}>
                  <div style={{ height: '100px' }}></div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {!loading && total > 0 && (
        <div className="pagination-container">
          <div className="pagination-info">
            Mostrando <strong>{results.length}</strong> de <strong>{total}</strong> resultados
          </div>

          <div className="pagination-controls">
            <button
              className="pagination-btn"
              disabled={page === 1}
              onClick={() => handlePageChange(page - 1)}
            >
              &laquo; Anterior
            </button>

            <div className="pagination-pages">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }

                return (
                  <button
                    key={pageNum}
                    className={`page-num ${page === pageNum ? 'active' : ''}`}
                    onClick={() => handlePageChange(pageNum)}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>

            <button
              className="pagination-btn"
              disabled={page === totalPages}
              onClick={() => handlePageChange(page + 1)}
            >
              Siguiente &raquo;
            </button>
          </div>

          <div className="pagination-limit">
            <select
              value={limit}
              onChange={handleLimitChange}
              aria-label="Resultados por página"
            >
              <option value="20">20 por página</option>
              <option value="50">50 por página</option>
              <option value="100">100 por página</option>
            </select>
          </div>
        </div>
      )}

      {selectedSongId && (
        <LyricModal songId={selectedSongId} onClose={() => setSelectedSongId(null)} />
      )}
    </div>
  );
};
