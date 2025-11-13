import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getMeetings, deleteMeeting } from '../api';
import './Dashboard.css';

function Dashboard() {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadMeetings();
  }, []);

  const loadMeetings = async () => {
    try {
      setLoading(true);
      const data = await getMeetings();
      setMeetings(data);
      setError('');
    } catch (err) {
      setError('Failed to load meetings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (meetingId, title) => {
    if (!window.confirm(`Are you sure you want to delete "${title}"?`)) {
      return;
    }

    try {
      await deleteMeeting(meetingId);
      setMeetings(meetings.filter(m => m.meetingId !== meetingId));
    } catch (err) {
      alert('Failed to delete meeting');
      console.error(err);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const filteredMeetings = meetings.filter(meeting =>
    meeting.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="loading">Loading meetings...</div>;
  }

  return (
    <div className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <h1>Meeting Dashboard</h1>
          <Link to="/upload" className="btn btn-primary">
            + New Meeting
          </Link>
        </div>

        {error && <div className="error">{error}</div>}

        <div className="search-bar">
          <input
            type="text"
            placeholder="Search meetings..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {filteredMeetings.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h2>No meetings found</h2>
            <p>
              {searchTerm
                ? 'Try a different search term'
                : 'Upload your first meeting to get started'}
            </p>
            {!searchTerm && (
              <Link to="/upload" className="btn btn-primary">
                Upload Meeting
              </Link>
            )}
          </div>
        ) : (
          <div className="meetings-grid">
            {filteredMeetings.map((meeting) => (
              <div key={meeting.meetingId} className="meeting-card card">
                <div className="meeting-header">
                  <h3>{meeting.title}</h3>
                  <span className="meeting-date">{formatDate(meeting.date)}</span>
                </div>

                <div className="meeting-summary">
                  <p>
                    {meeting.summary.length > 150
                      ? meeting.summary.substring(0, 150) + '...'
                      : meeting.summary}
                  </p>
                </div>

                <div className="meeting-stats">
                  <span className="stat">
                    <strong>{meeting.decisions?.length || 0}</strong> Decisions
                  </span>
                  <span className="stat">
                    <strong>{meeting.actionItems?.length || 0}</strong> Action Items
                  </span>
                </div>

                <div className="meeting-actions">
                  <Link
                    to={`/meeting/${meeting.meetingId}`}
                    className="btn btn-primary btn-sm"
                  >
                    View Details
                  </Link>
                  <button
                    onClick={() => handleDelete(meeting.meetingId, meeting.title)}
                    className="btn btn-danger btn-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
