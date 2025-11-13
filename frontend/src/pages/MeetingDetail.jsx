import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getMeeting, downloadSummary, deleteMeeting } from '../api';
import './MeetingDetail.css';

function MeetingDetail() {
  const { meetingId } = useParams();
  const navigate = useNavigate();
  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadMeeting();
  }, [meetingId]);

  const loadMeeting = async () => {
    try {
      setLoading(true);
      const data = await getMeeting(meetingId);
      setMeeting(data);
      setError('');
    } catch (err) {
      setError('Failed to load meeting details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    downloadSummary(meetingId);
  };

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete "${meeting.title}"?`)) {
      return;
    }

    try {
      await deleteMeeting(meetingId);
      navigate('/dashboard');
    } catch (err) {
      alert('Failed to delete meeting');
      console.error(err);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return <div className="loading">Loading meeting details...</div>;
  }

  if (error || !meeting) {
    return (
      <div className="container">
        <div className="error">{error || 'Meeting not found'}</div>
        <Link to="/dashboard" className="btn btn-secondary">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="meeting-detail">
      <div className="container">
        <div className="detail-header">
          <Link to="/dashboard" className="back-link">
            ← Back to Dashboard
          </Link>
          <div className="header-actions">
            <button onClick={handleDownload} className="btn btn-primary">
              📥 Download Summary
            </button>
            <button onClick={handleDelete} className="btn btn-danger">
              🗑️ Delete
            </button>
          </div>
        </div>

        <div className="meeting-info card">
          <h1>{meeting.title}</h1>
          <p className="meeting-meta">
            <span>📅 {formatDate(meeting.date)}</span>
            <span>📎 {meeting.fileName}</span>
          </p>
        </div>

        <div className="summary-section card">
          <h2>📝 Summary</h2>
          <p className="summary-text">{meeting.summary}</p>
        </div>

        <div className="decisions-section card">
          <h2>✅ Decisions ({meeting.decisions?.length || 0})</h2>
          {meeting.summary.includes('no transcript') ? (
            <div className="error">
              ⚠️ Transcription failed. Please check if the audio file is valid and try uploading again.
            </div>
          ) : meeting.decisions && meeting.decisions.length > 0 ? (
            <ul className="decisions-list">
              {meeting.decisions.map((decision, index) => (
                <li key={index}>{decision}</li>
              ))}
            </ul>
          ) : (
            <p className="empty-message">No decisions recorded</p>
          )}
        </div>

        <div className="action-items-section card">
          <h2>🎯 Action Items ({meeting.actionItems?.length || 0})</h2>
          {meeting.summary.includes('no transcript') ? (
            <div className="error">
              ⚠️ Transcription failed. Please check if the audio file is valid and try uploading again.
            </div>
          ) : meeting.actionItems && meeting.actionItems.length > 0 ? (
            <div className="action-items-list">
              {meeting.actionItems.map((item, index) => (
                <div key={index} className="action-item">
                  <div className="action-task">
                    <strong>{index + 1}.</strong> {item.task}
                  </div>
                  <div className="action-meta">
                    {item.owner && (
                      <span className="action-owner">
                        👤 {item.owner}
                      </span>
                    )}
                    {item.due_date && (
                      <span className="action-due">
                        📅 {item.due_date}
                      </span>
                    )}
                  </div>
                  {item.notes && (
                    <div className="action-notes">
                      📌 {item.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-message">No action items recorded</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default MeetingDetail;
