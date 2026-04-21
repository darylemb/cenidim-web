import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';

export const Timeline = () => {
  const [timelineData, setTimelineData] = useState({ years: [], timeline: {} });
  const [loading, setLoading] = useState(true);
  const [selectedSong, setSelectedSong] = useState(null);
  const [lyrics, setLyrics] = useState('');
  const [loadingLyrics, setLoadingLyrics] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiService
      .getTimeline()
      .then((data) => {
        setTimelineData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading timeline:', err);
        setLoading(false);
      });
  }, []);

  const handleSongSelect = (e, year) => {
    const songId = e.target.value;
    if (!songId) return;

    setLoadingLyrics(true);
    const song = timelineData.timeline[year].find((s) => s.id === parseInt(songId));
    setSelectedSong(song);

    apiService
      .getSongDetail(songId)
      .then((data) => {
        setLyrics(data.lyrics);
        setLoadingLyrics(false);
      })
      .catch((err) => {
        console.error('Error loading lyrics:', err);
        setLyrics('Error al cargar la letra.');
        setLoadingLyrics(false);
      });
  };

  if (loading) {
    return (
      <div className="content-area">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Cargando cronología...</p>
        </div>
      </div>
    );
  }

  // Group years into "staves" (rows of 4 measures)
  const staves = [];
  for (let i = 0; i < timelineData.years.length; i += 4) {
    staves.push(timelineData.years.slice(i, i + 4));
  }

  return (
    <div className="content-area">
      <div className="page-header-flex">
        <h2 className="page-title">Cronología Musical</h2>
        <div className="total-indicator">
          <strong>{timelineData.years.length}</strong> años registrados
        </div>
      </div>

      <div className="timeline-flow">
        <div className="timeline-intro">
          <p>Recorre los años del archivo sonoro y selecciona una pista para ver su letra.</p>
        </div>

        {staves.map((staffYears, staffIndex) => (
          <section
            key={staffIndex}
            className="timeline-row"
            style={{ '--row-delay': `${staffIndex * 120}ms` }}
          >
            <div className="timeline-row-line" aria-hidden="true"></div>

            <div className="timeline-cards-grid">
              {staffYears.map((year, yearIndex) => {
                const shortYearMatch = year.match(/\d{4}/);
                const shortYear = shortYearMatch ? shortYearMatch[0] : year;
                const hasMetadata = year.length > 6;
                const songsInYear = timelineData.timeline[year] || [];

                return (
                  <article
                    key={year}
                    className="timeline-card"
                    style={{ '--card-delay': `${yearIndex * 90}ms` }}
                  >
                    <div className="timeline-dot" aria-hidden="true"></div>

                    <div className="year-label-group">
                      <div className="measure-year">{shortYear}</div>
                      {hasMetadata && <div className="measure-metadata">{year}</div>}
                    </div>

                    <div className="timeline-card-body">
                      <div className="timeline-count">{songsInYear.length} canciones</div>
                      <div className="song-selector-container">
                        <select
                          className="stylized-select timeline-select"
                          onChange={(e) => handleSongSelect(e, year)}
                          value=""
                        >
                          <option value="" disabled>
                            Seleccionar pista
                          </option>
                          {songsInYear.map((song) => (
                            <option key={song.id} value={song.id}>
                              {song.title.length > 30
                                ? song.title.substring(0, 27) + '...'
                                : song.title}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      {selectedSong && (
        <div className="lyrics-modal-overlay" onClick={() => setSelectedSong(null)}>
          <div className="lyrics-modal" onClick={(e) => e.stopPropagation()}>
            <button className="close-modal" onClick={() => setSelectedSong(null)}>
              &times;
            </button>
            <div className="lyrics-content">
              <h3>{selectedSong.title}</h3>
              <p className="album-info">
                {selectedSong.album} ({selectedSong.year})
              </p>
              <hr />
              {loadingLyrics ? (
                <div className="loader small"></div>
              ) : (
                <pre>{lyrics || 'Letra no disponible'}</pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
