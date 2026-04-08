import React from 'react';
import { Header } from './Header';
import { NavBar } from './NavBar';

export const CombinedHeader = (props) => {
  const { user, onLogout, onLoginClick, ...navProps } = props;
  return (
    <div className="combined-header">
      <Header user={user} onLogout={onLogout} onLoginClick={onLoginClick} />
      <NavBar {...navProps} user={user} />
    </div>
  );
};
