import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Configurations from './pages/Configurations';
import FileSelection from './pages/FileSelection';
import PipelineRuns from './pages/PipelineRuns';
import Results from './pages/Results';
import Subscribers from './pages/Subscribers';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="navbar-brand">
            <h1>UT360 Pipeline Manager</h1>
          </div>
          <div className="navbar-menu">
            <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
              Dashboard
            </NavLink>
            <NavLink to="/file-selection" className={({ isActive }) => isActive ? 'active' : ''}>
              File Selection
            </NavLink>
            <NavLink to="/configurations" className={({ isActive }) => isActive ? 'active' : ''}>
              Configurations
            </NavLink>
            <NavLink to="/runs" className={({ isActive }) => isActive ? 'active' : ''}>
              Pipeline Runs
            </NavLink>
            <NavLink to="/results" className={({ isActive }) => isActive ? 'active' : ''}>
              Results
            </NavLink>
            <NavLink to="/subscribers" className={({ isActive }) => isActive ? 'active' : ''}>
              Subscribers
            </NavLink>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/file-selection" element={<FileSelection />} />
            <Route path="/configurations" element={<Configurations />} />
            <Route path="/runs" element={<PipelineRuns />} />
            <Route path="/results" element={<Results />} />
            <Route path="/subscribers" element={<Subscribers />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
