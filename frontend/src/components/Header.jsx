import React from 'react';

export const Header = ({ user, onLogout, onLoginClick }) => {
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
      <div className="right-logos" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h3 title="Centro Nacional de Investigación, Documentación e Información Musical">
          <span>🏛</span> CENIDIM
        </h3>
        {user ? (
          <div className="header-user">
            <span className={`role-badge role-${user.role}`}>{user.role}</span>
            <span className="header-username">{user.username}</span>
            <button className="btn-sm btn-secondary" onClick={onLogout}>
              Salir
            </button>
          </div>
        ) : (
          <button className="btn-sm nav-action-btn" onClick={onLoginClick}>
            Iniciar sesión
          </button>
        )}
      </div>
    </header>
  );
};
