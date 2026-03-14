import React from 'react';

export const Header = () => {
  return (
    <header className="app-header" aria-label="Cabecera institucional">
      <div className="header-branding">
        <div className="logo-icon-small" aria-hidden="true">
          𝄢
        </div>
        <div className="logo-text-small">
          <h2>CENIDIM</h2>
          <span className="sub-text">SECRETARÍA DE CULTURA</span>
        </div>
      </div>
      <div className="right-logos">
        <h3 title="Centro Nacional de Investigación, Documentación e Información Musical">
          <span>🏛</span> CENIDIM
        </h3>
      </div>
    </header>
  );
};
