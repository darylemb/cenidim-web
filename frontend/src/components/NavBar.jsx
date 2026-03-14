import React from 'react';

export const NavBar = ({ activeTab, setActiveTab }) => {
  const links = ['Buscador', 'Dashboards'];

  return (
    <nav className="main-nav">
      {links.map((link) => (
        <span
          key={link}
          className={link === activeTab ? 'active' : ''}
          onClick={() => setActiveTab(link)}
        >
          {link}
        </span>
      ))}
    </nav>
  );
};
