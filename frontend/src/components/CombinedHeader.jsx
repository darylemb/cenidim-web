import React from 'react';
import { Header } from './Header';
import { NavBar } from './NavBar';

export const CombinedHeader = (props) => {
  return (
    <div className="combined-header">
      <Header />
      <NavBar {...props} />
    </div>
  );
};
