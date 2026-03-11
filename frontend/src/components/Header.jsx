import React from 'react';

export const Header = () => {
  return (
    <header className="app-header">
      {/* Logos placeholders that match the structure of the image */}
      <div className="left-logos">
        <h2 style={{color: 'var(--cenidim-rojo)', fontWeight: 'bold', margin: 0}}>
          CULTURA <span style={{fontSize: '12px', color: '#666', fontWeight: 'normal', display: 'block'}}>SECRETARÍA DE CULTURA</span>
        </h2>
      </div>
      <div className="right-logos">
        <h3 style={{color: '#666', fontWeight: 'bold', margin: 0}}>
          <span style={{fontSize: '18px', marginRight: '5px'}}>🏛</span> INBAL
        </h3>
      </div>
    </header>
  );
};
