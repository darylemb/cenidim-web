import React from 'react';

export const HeroBanner = () => {
  return (
    <div className="hero-banner">
      <div className="banner-left">
        <div className="logo-text">
          <div className="logo-icon">𝄢</div>
          <h1>CENIDIM</h1>
        </div>
        <h2>
          Centro Nacional de Investigación,
          <br />Documentación e Información Musical
          <br />“Carlos Chávez”
        </h2>
      </div>
      <div className="banner-right aniversario">
        <div className="number">50</div>
        <div className="text">ANIVERSARIO</div>
      </div>
    </div>
  );
};
