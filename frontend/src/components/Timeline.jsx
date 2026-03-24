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
    apiService.getTimeline()
      .then(data => {
        setTimelineData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading timeline:', err);
        setLoading(false);
      });
  }, []);

  const handleSongSelect = (e, year) => {
    const songId = e.target.value;
    if (!songId) return;
    
    setLoadingLyrics(true);
    const song = timelineData.timeline[year].find(s => s.id === parseInt(songId));
    setSelectedSong(song);
    
    apiService.getSongDetail(songId)
      .then(data => {
        setLyrics(data.lyrics);
        setLoadingLyrics(false);
      })
      .catch(err => {
        console.error('Error loading lyrics:', err);
        setLyrics('Error al cargar la letra.');
        setLoadingLyrics(false);
      });
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loader"></div>
        <p>Cargando partitura...</p>
      </div>
    );
  }

  // Group years into "staves" (rows of 4 measures)
  const staves = [];
  for (let i = 0; i < timelineData.years.length; i += 4) {
    staves.push(timelineData.years.slice(i, i + 4));
  }

  return (
    <div className="timeline-container">
      <h2 className="page-title">Cronología Musical</h2>
      
      <div className="pentagram-area">
        {staves.map((staffYears, staffIndex) => (
          <div key={staffIndex} className="staff-row">
            <div className="staff-lines">
              <div className="line"></div>
              <div className="line"></div>
              <div className="line"></div>
              <div className="line"></div>
              <div className="line"></div>
            </div>
            
            <div className="measures-container">
              {staffYears.map((year) => {
                const shortYearMatch = year.match(/\d{4}/);
                const shortYear = shortYearMatch ? shortYearMatch[0] : year;
                const hasMetadata = year.length > 6;

                return (
                  <div key={year} className="measure">
                    <div className="year-label-group">
                      <div className="measure-year">{shortYear}</div>
                      {hasMetadata && <div className="measure-metadata">{year}</div>}
                    </div>
                    <div className="song-selector-container">
                      <select 
                        className="stylized-select" 
                        onChange={(e) => handleSongSelect(e, year)}
                        value=""
                      >
                        <option value="" disabled>Canciones ({timelineData.timeline[year].length})</option>
                        {timelineData.timeline[year].map(song => (
                          <option key={song.id} value={song.id}>
                            {song.title.length > 30 ? song.title.substring(0, 27) + '...' : song.title}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="bar-line"></div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {selectedSong && (
        <div className="lyrics-modal-overlay" onClick={() => setSelectedSong(null)}>
          <div className="lyrics-modal" onClick={e => e.stopPropagation()}>
            <button className="close-modal" onClick={() => setSelectedSong(null)}>&times;</button>
            <div className="lyrics-content">
              <h3>{selectedSong.title}</h3>
              <p className="album-info">{selectedSong.album} ({selectedSong.year})</p>
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
