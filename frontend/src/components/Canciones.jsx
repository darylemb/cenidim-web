import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

// Modal component to show lyrics
const LyricModal = ({ songId, onClose }) => {
  const [song, setSong] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiService
      .getSongDetail(songId)
      .then((data) => {
        setSong(data);
        setLoading(false);
      })
      .catch(() => {
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

const CLASIFICACION_LABELS = {
  '': 'Todas las clasificaciones',
  ESPAÑOL_ESTANDAR: 'Español Estándar',
  ESPAÑOL_REGIONAL: 'Español Regional',
  LENGUA_INDIGENA: 'Lengua Indígena',
};

const CLASIFICACION_BADGE = {
  ESPAÑOL_ESTANDAR: 'badge-estandar',
  ESPAÑOL_REGIONAL: 'badge-regional',
  LENGUA_INDIGENA: 'badge-indigena',
};

const ORDER_BY_OPTIONS = {
  id: 'ID',
  clave: 'Clave',
  title: 'Pista',
  album: 'Álbum',
  year: 'Año',
  filename: 'Archivo',
  clasificacion: 'Clasificación',
};

export const Canciones = ({
  results = [],
  total,
  page = 1,
  limit = 20,
  loading = false,
  handleReset,
  performSearch,
  query,
  field,
  clasificacion = '',
  setClasificacion,
  orderBy = 'id',
  setOrderBy,
  orderDir = 'asc',
  setOrderDir,
}) => {
  const [selectedSongId, setSelectedSongId] = useState(null);

  const renderTruncatedText = (value) => {
    const text = value && String(value).trim() ? String(value) : '—';
    return (
      <span className="table-cell-text" title={text}>
        {text}
      </span>
    );
  };

  const displayTotal = total ?? results.length;
  const totalPages = Math.ceil(displayTotal / limit);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      performSearch(query, field, newPage, limit, clasificacion, orderBy, orderDir);
      // No scrollTo — table stays in view
    }
  };

  const handleLimitChange = (e) => {
    const newLimit = parseInt(e.target.value, 10);
    performSearch(query, field, 1, newLimit, clasificacion, orderBy, orderDir);
  };

  const handleClasificacionChange = (e) => {
    const val = e.target.value;
    setClasificacion(val);
    performSearch(query, field, 1, limit, val, orderBy, orderDir);
  };

  const handleOrderByChange = (e) => {
    const val = e.target.value;
    setOrderBy(val);
    performSearch(query, field, 1, limit, clasificacion, val, orderDir);
  };

  const handleOrderDirChange = (e) => {
    const val = e.target.value;
    setOrderDir(val);
    performSearch(query, field, 1, limit, clasificacion, orderBy, val);
  };

  return (
    <div className="content-area">
      <div className="page-header-flex">
        <h2 className="page-title">Canciones</h2>
        <div className="total-indicator">
          <strong>{displayTotal}</strong> canciones encontradas
        </div>
      </div>

      {/* Classification filter */}
      <div className="filter-bar">
        <label htmlFor="clasificacion-filter" className="filter-label">
          Clasificación de lengua:
        </label>
        <select
          id="clasificacion-filter"
          className="clasificacion-select"
          value={clasificacion}
          onChange={handleClasificacionChange}
          aria-label="Filtrar por clasificación de lengua"
        >
          {Object.entries(CLASIFICACION_LABELS).map(([val, label]) => (
            <option key={val} value={val}>
              {label}
            </option>
          ))}
        </select>

        <label htmlFor="order-by-filter" className="filter-label">
          Ordenar por:
        </label>
        <select
          id="order-by-filter"
          className="clasificacion-select"
          value={orderBy}
          onChange={handleOrderByChange}
          aria-label="Campo de ordenamiento"
        >
          {Object.entries(ORDER_BY_OPTIONS).map(([val, label]) => (
            <option key={val} value={val}>
              {label}
            </option>
          ))}
        </select>

        <select
          id="order-dir-filter"
          className="clasificacion-select"
          value={orderDir}
          onChange={handleOrderDirChange}
          aria-label="Dirección de ordenamiento"
        >
          <option value="asc">Ascendente</option>
          <option value="desc">Descendente</option>
        </select>
      </div>

      <div className="results-table-container">
        {loading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
            <p>Buscando en el archivo del CENIDIM...</p>
          </div>
        )}
        <div className="table-scroll-wrapper">
          <table
            className={`results-table results-table--wide ${loading ? 'loading-opacity' : ''}`}
          >
            <thead>
              <tr>
                <th>Clave</th>
                <th>Pista</th>
                <th>Álbum</th>
                <th>Subtítulo</th>
                <th>Intérprete Principal</th>
                <th>Intérpretes Invitados</th>
                <th>Intérprete Participante</th>
                <th>Soporte Físico</th>
                <th>Editora</th>
                <th>N° Catálogo</th>
                <th>Ciudad</th>
                <th>País</th>
                <th>Año</th>
                <th>Pistas</th>
                <th>Observaciones</th>
                <th>Archivo</th>
                <th>Clasificación</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {!loading && results.length > 0 ? (
                results.map((song) => (
                  <tr key={song.id}>
                    <td data-label="Clave">{song.fonograma_id}</td>
                    <td data-label="Pista" className="table-cell-truncate">
                      {renderTruncatedText(song.title)}
                    </td>
                    <td data-label="Álbum" className="table-cell-truncate">
                      {renderTruncatedText(song.album)}
                    </td>
                    <td data-label="Subtítulo" className="table-cell-truncate">
                      {renderTruncatedText(song.subtitulo)}
                    </td>
                    <td data-label="Intérprete Principal" className="table-cell-truncate">
                      {renderTruncatedText(song.interprete_principal)}
                    </td>
                    <td data-label="Intérpretes Invitados" className="table-cell-truncate">
                      {renderTruncatedText(song.interpretes_invitados)}
                    </td>
                    <td data-label="Intérprete Participante" className="table-cell-truncate">
                      {renderTruncatedText(song.interprete_participante)}
                    </td>
                    <td data-label="Soporte Físico" className="table-cell-truncate">
                      {renderTruncatedText(song.soporte_fisico)}
                    </td>
                    <td data-label="Editora" className="table-cell-truncate">
                      {renderTruncatedText(song.editora)}
                    </td>
                    <td data-label="N° Catálogo" className="table-cell-truncate">
                      {renderTruncatedText(song.numero_catalogo)}
                    </td>
                    <td data-label="Ciudad" className="table-cell-truncate">
                      {renderTruncatedText(song.ciudad_edicion)}
                    </td>
                    <td data-label="País" className="table-cell-truncate">
                      {renderTruncatedText(song.pais_edicion)}
                    </td>
                    <td data-label="Año" className="table-cell-truncate">
                      {renderTruncatedText(song.year)}
                    </td>
                    <td data-label="Pistas" className="table-cell-truncate cell-pistas">
                      {renderTruncatedText(song.pistas)}
                    </td>
                    <td data-label="Observaciones" className="table-cell-truncate">
                      {renderTruncatedText(song.observaciones)}
                    </td>
                    <td data-label="Archivo" className="table-cell-truncate">
                      {renderTruncatedText(song.filename)}
                    </td>
                    <td data-label="Clasificación">
                      <span
                        className={`clasificacion-badge ${CLASIFICACION_BADGE[song.clasificacion || 'ESPAÑOL_ESTANDAR'] || 'badge-estandar'}`}
                      >
                        {CLASIFICACION_LABELS[song.clasificacion || 'ESPAÑOL_ESTANDAR'] ||
                          song.clasificacion ||
                          'Español Estándar'}
                      </span>
                    </td>
                    <td data-label="Acción">
                      {song.filename ? (
                        <button className="action-btn" onClick={() => setSelectedSongId(song.id)}>
                          Ver Letra
                        </button>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                ))
              ) : !loading ? (
                <tr>
                  <td colSpan="18" style={{ textAlign: 'center', padding: '4rem' }}>
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
                  <td colSpan="18" style={{ textAlign: 'center', padding: '2rem' }}>
                    <div style={{ height: '100px' }}></div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {!loading && displayTotal > 0 && (
        <div className="pagination-container">
          <div className="pagination-info">
            Mostrando <strong>{results.length}</strong> de <strong>{displayTotal}</strong>{' '}
            resultados
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
            <select value={limit} onChange={handleLimitChange} aria-label="Resultados por página">
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
