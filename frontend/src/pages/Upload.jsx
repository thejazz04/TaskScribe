import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadMeeting } from '../api';
import './Upload.css';

function Upload() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [userName, setUserName] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file');
      return;
    }

    if (!title.trim()) {
      setError('Please enter a meeting title');
      return;
    }

    if (!userName.trim()) {
      setError('Please enter your name');
      return;
    }

    setUploading(true);
    setError('');
    setProgress('Uploading file...');

    try {
      setProgress('Processing meeting (this may take several minutes)...');
      const result = await uploadMeeting(file, title, userName);
      
      setProgress('Complete! Redirecting...');
      setTimeout(() => {
        navigate(`/meeting/${result.meeting.meetingId}`);
      }, 1000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload meeting');
      setUploading(false);
      setProgress('');
    }
  };

  return (
    <div className="upload-page">
      <div className="container">
        <div className="upload-card card">
          <h1>Upload Meeting Recording</h1>
          <p className="description">
            Upload your meeting recording to generate an AI-powered summary with decisions and action items.
          </p>

          {error && <div className="error">{error}</div>}
          {progress && <div className="progress-message">{progress}</div>}

          <form onSubmit={handleSubmit} className="upload-form">
            <div className="form-group">
              <label htmlFor="userName">Your Name *</label>
              <input
                type="text"
                id="userName"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder="e.g., John Doe"
                disabled={uploading}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="title">Meeting Title *</label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Team Sync - Nov 13"
                disabled={uploading}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="file">Meeting Recording *</label>
              <div className="file-input-wrapper">
                <input
                  type="file"
                  id="file"
                  onChange={handleFileChange}
                  accept=".mp4,.mp3,.wav,.webm,.m4a,.avi,.mov"
                  disabled={uploading}
                  required
                />
                {file && (
                  <div className="file-info">
                    <span className="file-name">📎 {file.name}</span>
                    <span className="file-size">
                      ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                    </span>
                  </div>
                )}
              </div>
              <small className="help-text">
                Supported formats: MP4, MP3, WAV, WEBM, M4A, AVI, MOV (Max 500MB)
              </small>
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={uploading}
              >
                {uploading ? 'Processing...' : 'Upload & Summarize'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => navigate('/dashboard')}
                disabled={uploading}
              >
                Cancel
              </button>
            </div>
          </form>

          {uploading && (
            <div className="processing-info">
              <div className="spinner"></div>
              <p>
                <strong>Processing your meeting...</strong><br />
                This includes transcription and AI summarization.<br />
                Please wait, this may take several minutes depending on file size.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Upload;
