import { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { io } from 'socket.io-client';
import './MeetingRoom.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function MeetingRoom() {
  const { roomId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const userName = searchParams.get('name') || 'Anonymous';
  const isHost = searchParams.get('host') === 'true';
  
  const [participants, setParticipants] = useState([]);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isAudioOn, setIsAudioOn] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  
  const localVideoRef = useRef(null);
  const socketRef = useRef(null);
  const localStreamRef = useRef(null);
  const peerConnectionsRef = useRef({});
  const userId = useRef(Math.random().toString(36).substr(2, 9));
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);

  useEffect(() => {
    initializeMedia();
    initializeSocket();
    
    return () => {
      cleanup();
    };
  }, []);

  const initializeMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      });
      
      localStreamRef.current = stream;
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // Verify audio track exists
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length === 0) {
        alert('Warning: No audio track detected. Recording may not have sound.');
      } else {
        console.log('Audio track active:', audioTracks[0].label);
      }
    } catch (err) {
      console.error('Error accessing media devices:', err);
      alert('Could not access camera/microphone. Please grant permissions.');
    }
  };

  const initializeSocket = () => {
    socketRef.current = io(API_URL);
    
    socketRef.current.on('connect', () => {
      console.log('Connected to server');
      socketRef.current.emit('join-room', {
        roomId,
        userName,
        userId: userId.current
      });
    });

    socketRef.current.on('user-joined', (data) => {
      console.log('User joined:', data);
      setParticipants(prev => [...prev, { userId: data.userId, userName: data.userName }]);
    });

    socketRef.current.on('user-left', (data) => {
      console.log('User left:', data);
      setParticipants(prev => prev.filter(p => p.userId !== data.userId));
    });

    socketRef.current.on('room-users', (data) => {
      setParticipants(data.participants);
    });

    socketRef.current.on('recording-started', () => {
      setIsRecording(true);
    });

    socketRef.current.on('recording-stopped', () => {
      setIsRecording(false);
    });
  };

  const toggleVideo = () => {
    if (localStreamRef.current) {
      const videoTrack = localStreamRef.current.getVideoTracks()[0];
      videoTrack.enabled = !videoTrack.enabled;
      setIsVideoOn(videoTrack.enabled);
    }
  };

  const toggleAudio = () => {
    if (localStreamRef.current) {
      const audioTrack = localStreamRef.current.getAudioTracks()[0];
      audioTrack.enabled = !audioTrack.enabled;
      setIsAudioOn(audioTrack.enabled);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const startRecording = () => {
    if (!localStreamRef.current) return;

    try {
      // Try MP4 first, fallback to WebM
      let options;
      let mimeType;
      
      if (MediaRecorder.isTypeSupported('video/mp4')) {
        options = { mimeType: 'video/mp4' };
        mimeType = 'video/mp4';
      } else if (MediaRecorder.isTypeSupported('video/webm;codecs=h264')) {
        options = { mimeType: 'video/webm;codecs=h264' };
        mimeType = 'video/webm';
      } else {
        options = { mimeType: 'video/webm;codecs=vp8,opus' };
        mimeType = 'video/webm';
      }

      mediaRecorderRef.current = new MediaRecorder(localStreamRef.current, options);
      recordedChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const blob = new Blob(recordedChunksRef.current, { type: mimeType });
        await saveRecording(blob, mimeType);
      };

      mediaRecorderRef.current.start();
      socketRef.current.emit('start-recording', { roomId });
    } catch (err) {
      console.error('Error starting recording:', err);
      alert('Failed to start recording');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      socketRef.current.emit('stop-recording', { roomId });
    }
  };

  const saveRecording = async (blob, mimeType) => {
    try {
      // Determine file extension based on mime type
      const extension = mimeType.includes('mp4') ? 'mp4' : 'webm';
      
      // Create download link
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `meeting-${roomId}-${Date.now()}.${extension}`;
      
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 100);

      alert(`Recording downloaded as ${extension.toUpperCase()}! You can upload it later from the Upload page to get AI summary.`);
    } catch (err) {
      console.error('Error saving recording:', err);
      alert('Failed to download recording.');
    }
  };

  const leaveMeeting = () => {
    // Stop recording if active
    if (isRecording && mediaRecorderRef.current) {
      if (window.confirm('Recording is in progress. Stop and download before leaving?')) {
        stopRecording();
        // Give time for download to start
        setTimeout(() => {
          cleanup();
          navigate('/dashboard');
        }, 1000);
      } else {
        return; // Don't leave if user cancels
      }
    } else {
      cleanup();
      navigate('/dashboard');
    }
  };

  const cleanup = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
    }
    
    if (socketRef.current) {
      socketRef.current.emit('leave-room', {
        roomId,
        userId: userId.current
      });
      socketRef.current.disconnect();
    }
    
    Object.values(peerConnectionsRef.current).forEach(pc => pc.close());
  };

  const copyMeetingId = () => {
    navigator.clipboard.writeText(roomId);
    alert('Meeting ID copied to clipboard!');
  };

  return (
    <div className="meeting-room">
      <div className="meeting-header">
        <div className="meeting-info">
          <h2>Meeting: {roomId}</h2>
          <span className="participant-count">👥 {participants.length + 1} participants</span>
        </div>
        <button onClick={copyMeetingId} className="btn btn-secondary btn-sm">
          📋 Copy Meeting ID
        </button>
      </div>

      <div className="video-grid">
        <div className="video-container local">
          <video ref={localVideoRef} autoPlay muted playsInline />
          <div className="video-label">{userName} (You)</div>
          {!isVideoOn && <div className="video-off-overlay">📷 Camera Off</div>}
        </div>

        {participants.map((participant) => (
          <div key={participant.userId} className="video-container">
            <div className="video-placeholder">
              <div className="avatar">{participant.userName[0].toUpperCase()}</div>
            </div>
            <div className="video-label">{participant.userName}</div>
          </div>
        ))}
      </div>

      <div className="meeting-controls">
        <button
          onClick={toggleAudio}
          className={`control-btn ${!isAudioOn ? 'off' : ''}`}
          title={isAudioOn ? 'Mute' : 'Unmute'}
        >
          {isAudioOn ? '🎤' : '🔇'}
        </button>

        <button
          onClick={toggleVideo}
          className={`control-btn ${!isVideoOn ? 'off' : ''}`}
          title={isVideoOn ? 'Turn off camera' : 'Turn on camera'}
        >
          {isVideoOn ? '📹' : '📷'}
        </button>

        {isHost && (
          <button
            onClick={toggleRecording}
            className={`control-btn ${isRecording ? 'recording' : ''}`}
            title={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {isRecording ? '⏹️' : '⏺️'}
          </button>
        )}

        <button
          onClick={() => setShowChat(!showChat)}
          className="control-btn"
          title="Chat"
        >
          💬
        </button>

        <button
          onClick={leaveMeeting}
          className="control-btn leave-btn"
          title="Leave meeting"
        >
          📞 Leave
        </button>
      </div>

      {isRecording && (
        <div className="recording-indicator">
          <span className="rec-dot"></span>
          Recording in progress...
        </div>
      )}
    </div>
  );
}

export default MeetingRoom;
