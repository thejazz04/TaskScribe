import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import Upload from './pages/Upload';
import Record from './pages/Record';
import Dashboard from './pages/Dashboard';
import MeetingDetail from './pages/MeetingDetail';
import JoinMeeting from './pages/JoinMeeting';
import MeetingRoom from './pages/MeetingRoom';
import './App.css';

function AppContent() {
  const location = useLocation();
  const isInMeetingRoom = location.pathname.startsWith('/room/');

  return (
    <div className="app">
      {!isInMeetingRoom && (
        <nav className="navbar">
          <div className="container">
            <Link to="/" className="logo">
              📝 Meeting Summarizer
            </Link>
            <div className="nav-links">
              <Link to="/">Home</Link>
              <Link to="/join">Live Meeting</Link>
              <Link to="/dashboard">Dashboard</Link>
              <Link to="/upload">Upload</Link>
              <Link to="/record">Record</Link>
            </div>
          </div>
        </nav>
      )}

      <main className={isInMeetingRoom ? '' : 'main-content'}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/join" element={<JoinMeeting />} />
          <Route path="/room/:roomId" element={<MeetingRoom />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/record" element={<Record />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/meeting/:meetingId" element={<MeetingDetail />} />
        </Routes>
      </main>

      {!isInMeetingRoom && (
        <footer className="footer">
          <div className="container">
            <p>&copy; 2025 Meeting Summarizer. Powered by TaskScribe AI.</p>
          </div>
        </footer>
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
