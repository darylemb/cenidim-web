import React, { useState } from 'react';

export const NavBar = ({
  activeTab,
  setActiveTab,
  query,
  setQuery,
  field,
  setField,
  performSearch,
  handleReset,
  limit,
  clasificacion,
  orderBy,
  orderDir,
  user,
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const publicLinks = ['Línea de tiempo', 'Canciones', 'Dashboards'];
  const links = user ? [...publicLinks, 'Admin'] : publicLinks;

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const handleTabClick = (link) => {
    setActiveTab(link);
    setIsMenuOpen(false);
  };

  const handleSearch = () => {
    performSearch(query, field, 1, limit, clasificacion, orderBy, orderDir);
    setIsMenuOpen(false);
  };

  return (
    <nav className="main-nav" aria-label="Navegación principal">
      <div className="nav-left">
        <button
          className="menu-toggle"
          onClick={toggleMenu}
          aria-expanded={isMenuOpen}
          aria-label={isMenuOpen ? 'Cerrar menú de navegación' : 'Abrir menú de navegación'}
        >
          <span className="hamburger-icon"></span>
        </button>

        <div className={`nav-links ${isMenuOpen ? 'open' : ''}`}>
          {links.map((link) => (
            <button
              key={link}
              className={link === activeTab ? 'active' : ''}
              onClick={() => handleTabClick(link)}
              aria-current={link === activeTab ? 'page' : undefined}
            >
              {link}
            </button>
          ))}
        </div>
      </div>

      <div className={`nav-search ${isMenuOpen ? 'open' : ''}`}>
        <select
          value={field}
          onChange={(e) => setField(e.target.value)}
          aria-label="Filtrar búsqueda por campo"
        >
          <option value="all">Filtro General</option>
          <option value="album">Álbum</option>
          <option value="title">Título</option>
          <option value="lyrics">Contenido (Letra)</option>
        </select>

        <input
          type="text"
          placeholder="Buscar canciones..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />

        <div className="nav-search-actions">
          <button className="nav-action-btn" onClick={handleSearch}>
            Buscar
          </button>
          <button className="nav-btn-reset" onClick={handleReset}>
            Reset
          </button>
        </div>
      </div>
    </nav>
  );
};
