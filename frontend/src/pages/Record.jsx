import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadMeeting } from '../api';
import './Record.css';

function Record() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [userName, setUserName] = useState('');
  const [recording, setRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: true,
        video: false
      });

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setRecordedBlob(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setRecording(true);
      setDuration(0);

      timerRef.current = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);

    } catch (err) {
      setError('Failed to access microphone. Please grant permission.');
      console.error(err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const handleUpload = async () => {
    if (!recordedBlob) {
      setError('No recording available');
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

    try {
      const file = new File([recordedBlob], `recording-${Date.now()}.webm`, {
        type: 'audio/webm'
      });

      const result = await uploadMeeting(file, title, userName);
      navigate(`/meeting/${result.meeting.meetingId}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload recording');
    } finally {
      setUploading(false);
    }
  };

  const handleDiscard = () => {
    setRecordedBlob(null);
    setDuration(0);
    chunksRef.current = [];
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="record-page">
      <div className="container">
        <div className="record-card card">
          <h1>🎙️ Record Meeting</h1>
          <p className="description">
            Record your meeting audio and get an AI-generated summary
          </p>

          {error && <div className="error">{error}</div>}

          <div className="record-controls">
            {!recording && !recordedBlob && (
              <button 
                onClick={startRecording} 
                className="btn btn-primary btn-large record-btn"
              >
                <span className="record-icon">●</span> Start Recording
              </button>
            )}

            {recording && (
              <div className="recording-active">
                <div className="recording-indicator">
                  <span className="pulse"></span>
                  Recording...
                </div>
                <div className="duration">{formatDuration(duration)}</div>
                <button 
                  onClick={stopRecording} 
                  className="btn btn-danger btn-large"
                >
                  ⏹ Stop Recording
                </button>
              </div>
            )}

            {recordedBlob && !recording && (
              <div className="recording-complete">
                <div className="success">
                  ✓ Recording complete! Duration: {formatDuration(duration)}
                </div>

                <div className="form-group">
                  <label htmlFor="userName">Your Name</label>
                  <input
                    type="text"
                    id="userName"
                    value={userName}
                    onChange={(e) => setUserName(e.target.value)}
                    placeholder="e.g., John Doe"
                    disabled={uploading}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="title">Meeting Title</label>
                  <input
                    type="text"
                    id="title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g., Team Sync - Nov 13"
                    disabled={uploading}
                  />
                </div>

                <div className="action-buttons">
                  <button 
                    onClick={handleUpload} 
                    className="btn btn-primary"
                    disabled={uploading}
                  >
                    {uploading ? 'Processing...' : '📤 Upload & Summarize'}
                  </button>
                  <button 
                    onClick={handleDiscard} 
                    className="btn btn-secondary"
                    disabled={uploading}
                  >
                    🗑️ Discard
                  </button>
                </div>

                {uploading && (
                  <div className="processing-info">
                    <div className="spinner"></div>
                    <p>Processing your recording... This may take several minutes.</p>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="tips">
            <h3>💡 Recording Tips</h3>
            <ul>
              <li>Ensure you're in a quiet environment</li>
              <li>Speak clearly and at a moderate pace</li>
              <li>Keep microphone close but not too close</li>
              <li>Recommended: 5-30 minute recordings</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Record;
