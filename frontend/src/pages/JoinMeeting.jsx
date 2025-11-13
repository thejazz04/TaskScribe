import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createRoom, getRoomInfo } from '../api';
import './JoinMeeting.css';

function JoinMeeting() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('join'); // 'join' or 'host'
  const [userName, setUserName] = useState('');
  const [roomId, setRoomId] = useState('');
  const [meetingTitle, setMeetingTitle] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleHostMeeting = async (e) => {
    e.preventDefault();
    
    if (!userName.trim()) {
      setError('Please enter your name');
      return;
    }

    if (!meetingTitle.trim()) {
      setError('Please enter a meeting title');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await createRoom(userName, meetingTitle);
      navigate(`/room/${response.roomId}?name=${encodeURIComponent(userName)}&host=true`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create meeting');
    } finally {
      setLoading(false);
    }
  };

  const handleJoinMeeting = async (e) => {
    e.preventDefault();
    
    if (!userName.trim()) {
      setError('Please enter your name');
      return;
    }

    if (!roomId.trim()) {
      setError('Please enter a meeting ID');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Verify room exists
      await getRoomInfo(roomId);
      navigate(`/room/${roomId}?name=${encodeURIComponent(userName)}`);
    } catch (err) {
      setError('Meeting not found. Please check the meeting ID.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="join-meeting-page">
      <div className="container">
        <div className="join-card card">
          <h1>📹 Live Meeting</h1>
          <p className="subtitle">Host or join a video meeting</p>

          <div className="mode-selector">
            <button
              className={`mode-btn ${mode === 'host' ? 'active' : ''}`}
              onClick={() => setMode('host')}
            >
              🎥 Host Meeting
            </button>
            <button
              className={`mode-btn ${mode === 'join' ? 'active' : ''}`}
              onClick={() => setMode('join')}
            >
              🚪 Join Meeting
            </button>
          </div>

          {error && <div className="error">{error}</div>}

          {mode === 'host' ? (
            <form onSubmit={handleHostMeeting} className="meeting-form">
              <div className="form-group">
                <label htmlFor="userName">Your Name *</label>
                <input
                  type="text"
                  id="userName"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  placeholder="e.g., John Doe"
                  required
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="meetingTitle">Meeting Title *</label>
                <input
                  type="text"
                  id="meetingTitle"
                  value={meetingTitle}
                  onChange={(e) => setMeetingTitle(e.target.value)}
                  placeholder="e.g., Team Standup"
                  required
                  disabled={loading}
                />
              </div>

              <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
                {loading ? 'Creating...' : '🎥 Start Meeting'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleJoinMeeting} className="meeting-form">
              <div className="form-group">
                <label htmlFor="userName">Your Name *</label>
                <input
                  type="text"
                  id="userName"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  placeholder="e.g., John Doe"
                  required
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="roomId">Meeting ID *</label>
                <input
                  type="text"
                  id="roomId"
                  value={roomId}
                  onChange={(e) => setRoomId(e.target.value.toUpperCase())}
                  placeholder="e.g., ABC123XY"
                  required
                  disabled={loading}
                  maxLength="8"
                />
                <small className="help-text">
                  Enter the 8-character meeting ID shared by the host
                </small>
              </div>

              <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
                {loading ? 'Joining...' : '🚪 Join Meeting'}
              </button>
            </form>
          )}

          <div className="features-info">
            <h3>✨ Features</h3>
            <ul>
              <li>🎥 HD Video & Audio</li>
              <li>🎙️ Record meetings automatically</li>
              <li>📝 AI-powered summaries after meeting</li>
              <li>👥 Multiple participants</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default JoinMeeting;
