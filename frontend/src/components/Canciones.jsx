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

export const Canciones = ({ results = [], loading = false, handleReset }) => {
  const [selectedSongId, setSelectedSongId] = useState(null);

  return (
    <div className="content-area">
      <h2 className="page-title">Canciones</h2>

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

      {/* Render modal if a song is selected */}
      {selectedSongId && (
        <LyricModal songId={selectedSongId} onClose={() => setSelectedSongId(null)} />
      )}
    </div>
  );
};
