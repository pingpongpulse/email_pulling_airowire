import { BrowserRouter as Router, Routes, Route, NavLink, useNavigate } from 'react-router-dom';
import { Mail, Send, Inbox as InboxIcon, LayoutDashboard, Plus } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import ThreadView from './pages/ThreadView';
import ComposeEmail from './pages/ComposeEmail';
import './index.css';

function Sidebar() {
  return (
    <div className="sidebar">
      <div className="brand">Airowire</div>
      <nav>
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
          <LayoutDashboard size={20} />
          Dashboard
        </NavLink>
        <NavLink to="/inbox" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <InboxIcon size={20} />
          Inbox
        </NavLink>
        <NavLink to="/sent" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Send size={20} />
          Sent
        </NavLink>
        
        <div style={{ marginTop: 'auto', paddingTop: '2rem' }}>
          <NavLink to="/compose" className="btn btn-primary" style={{ width: '100%', textDecoration: 'none' }}>
            <Plus size={20} style={{ marginRight: '0.5rem' }} /> Compose
          </NavLink>
        </div>
      </nav>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/inbox" element={<Dashboard />} /> 
            <Route path="/sent" element={<div className="page-title">Sent Mail (Coming Soon)</div>} />
            <Route path="/compose" element={<ComposeEmail />} />
            <Route path="/thread/:id" element={<ThreadView />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
