import React, { useEffect, useState, useRef } from 'react';
import { apiService } from '../services/api';

export const Timeline = () => {
  const [timelineData, setTimelineData] = useState({ years: [], timeline: {} });
  const [loading, setLoading] = useState(true);
  const [selectedSong, setSelectedSong] = useState(null);
  const [lyrics, setLyrics] = useState('');
  const [loadingLyrics, setLoadingLyrics] = useState(false);
  const [visibleYears, setVisibleYears] = useState(new Set());
  const timelineRef = useRef(null);

  useEffect(() => {
    setLoading(true);
    apiService
      .getTimeline()
      .then((data) => {
        setTimelineData(data);
        setLoading(false);
        // Initialize all years as visible after data loads
        setVisibleYears(new Set(data.years));
      })
      .catch((err) => {
        console.error('Error loading timeline:', err);
        setLoading(false);
      });
  }, []);

  // Intersection Observer for lazy loading animations
  useEffect(() => {
    if (!timelineRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const year = entry.target.dataset.year;
            setVisibleYears((prev) => new Set([...prev, year]));
          }
        });
      },
      {
        root: timelineRef.current,
        rootMargin: '100px',
        threshold: 0.1,
      }
    );

    const yearElements = timelineRef.current.querySelectorAll('.timeline-year-item');
    yearElements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, [timelineData.years]);

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

  return (
    <div className="content-area">
      <div className="page-header-flex">
        <h2 className="page-title">Cronología Musical</h2>
        <div className="total-indicator">
          <strong>{timelineData.years.length}</strong> años registrados
        </div>
      </div>

      <div className="timeline-intro">
        <p>Explora el archivo sonoro por año. Selecciona una canción para ver su letra.</p>
      </div>

      {/* Horizontal scrolling timeline container */}
      <div className="timeline-container" ref={timelineRef}>
        <div className="timeline-track">
          {timelineData.years.map((year, index) => {
            const songsInYear = timelineData.timeline[year] || [];
            const isVisible = visibleYears.has(year);
            const shortYearMatch = year.match(/\d{4}/);
            const shortYear = shortYearMatch ? shortYearMatch[0] : year;

            return (
              <div
                key={year}
                className={`timeline-year-item ${isVisible ? 'visible' : ''}`}
                data-year={year}
                style={{
                  '--year-index': index,
                  '--animation-delay': `${index * 50}ms`,
                }}
              >
                {/* Connecting line to next year */}
                {index < timelineData.years.length - 1 && (
                  <div className="timeline-connector">
                    <div className="connector-line"></div>
                    <div className="connector-dot"></div>
                  </div>
                )}

                {/* Year node */}
                <div className="timeline-year-node">
                  <div className="node-circle">
                    <span className="node-year">{shortYear}</span>
                  </div>
                  <div className="node-label">{year}</div>
                </div>

                {/* Song count badge */}
                <div className="timeline-year-badge">
                  <span className="badge-count">{songsInYear.length}</span>
                  <span className="badge-label">canciones</span>
                </div>

                {/* Song selector */}
                <div className="timeline-song-selector">
                  <select
                    className="timeline-select"
                    onChange={(e) => handleSongSelect(e, year)}
                    value=""
                  >
                    <option value="" disabled>
                      Seleccionar pista
                    </option>
                    {songsInYear.map((song) => (
                      <option key={song.id} value={song.id}>
                        {song.title.length > 35 ? song.title.substring(0, 32) + '...' : song.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Year summary bar at bottom */}
      <div className="timeline-summary">
        <div className="summary-track">
          {timelineData.years.map((year) => {
            const songsInYear = timelineData.timeline[year] || [];
            return (
              <div
                key={year}
                className="summary-segment"
                style={{
                  '--segment-width': `${Math.max(songsInYear.length * 3, 10)}%`,
                }}
                title={`${year}: ${songsInYear.length} canciones`}
              ></div>
            );
          })}
        </div>
      </div>

      {/* Lyrics modal */}
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
