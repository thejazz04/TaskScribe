import { Link } from 'react-router-dom';
import './Home.css';

function Home() {
  return (
    <div className="home">
      <div className="container">
        <div className="hero">
          <h1>Welcome to Meeting Summarizer</h1>
          <p className="subtitle">
            Transform your meeting recordings into actionable insights with AI-powered summarization
          </p>
          
          <div className="features">
            <div className="feature-card">
              <div className="feature-icon">🎥</div>
              <h3>Upload Recordings</h3>
              <p>Support for MP4, MP3, WAV, and more</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3>AI Summarization</h3>
              <p>Powered by advanced LLM models</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Extract Insights</h3>
              <p>Get summaries, decisions, and action items</p>
            </div>
          </div>

          <div className="cta-buttons">
            <Link to="/join" className="btn btn-primary btn-large">
              📹 Start Live Meeting
            </Link>
            <Link to="/upload" className="btn btn-secondary btn-large">
              📤 Upload Recording
            </Link>
          </div>
        </div>

        <div className="how-it-works">
          <h2>How It Works</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <h3>Upload</h3>
              <p>Upload your meeting recording file</p>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <h3>Process</h3>
              <p>AI transcribes and analyzes the content</p>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <h3>Review</h3>
              <p>Get structured summaries and action items</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
