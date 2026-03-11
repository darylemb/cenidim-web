import React, { useState } from 'react';
import './index.css';
import { Header } from './components/Header';
import { HeroBanner } from './components/HeroBanner';
import { NavBar } from './components/NavBar';
import { Buscador } from './components/Buscador';
import { DashboardView } from './components/DashboardView';

function App() {
  const [activeTab, setActiveTab] = useState("Buscador");

  return (
    <div className="App">
      <Header />
      <HeroBanner />
      <NavBar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main>
        {activeTab === "Buscador" ? (
          <Buscador />
        ) : activeTab === "Dashboards" ? (
          <DashboardView />
        ) : (
          <div className="content-area">
            <h2 className="page-title">{activeTab}</h2>
            <p>Sección en construcción. Por favor visite la sección del <strong>Buscador</strong> o <strong>Dashboards</strong>.</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
