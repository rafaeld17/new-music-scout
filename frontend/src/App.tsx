/**
 * Main App component (Simplified Phase 3)
 */

import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import AlbumList from './components/AlbumList';
import AlbumDetail from './components/AlbumDetail';
import SinglesList from './components/SinglesList';
import './App.css';

function Navigation() {
  const location = useLocation();

  return (
    <nav className="app-nav">
      <Link
        to="/"
        className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
      >
        Albums
      </Link>
      {/* New Singles temporarily hidden - artist extraction needs improvement
      <Link
        to="/singles"
        className={`nav-link ${location.pathname === '/singles' ? 'active' : ''}`}
      >
        New Singles
      </Link>
      */}
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div className="header-hero">
            <div className="header-content">
              <div className="logo-section">
                <div className="logo-bolt">⚡</div>
                <div>
                  <h1 className="app-title">NEW MUSIC SCOUT</h1>
                  <p className="app-subtitle">Progressive • Rock • Metal</p>
                </div>
              </div>
              <Navigation />
            </div>
          </div>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<AlbumList view="recent" />} />
            <Route path="/singles" element={<SinglesList />} />
            <Route path="/album/:artist/:album" element={<AlbumDetail />} />
          </Routes>
        </main>

        <footer className="app-footer">
          <p>Aggregating reviews from 6 trusted sources: Sonic Perspectives • MetalSucks • Metal Storm • The Prog Report • Heavy Music HQ • Rock & Blues Muse</p>
          <p className="footer-secondary">389 reviews • 74% with rich Spotify metadata • Updated weekly</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
