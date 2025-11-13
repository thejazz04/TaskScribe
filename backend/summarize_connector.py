"""
Connector to TaskScribe summarization model
Bridges the Flask backend with the existing meeting_summarizer_v2.py
"""
import sys
import os
from pathlib import Path

# Add parent directory (NLP) to Python path to import TaskScribe modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import the summarizer and pipeline
from meeting_summarizer_v2 import MeetingSummarizer
import complete_pipeline

# Global summarizer instance (loaded once for efficiency)
_summarizer = None

def get_summarizer():
    """Get or create the summarizer instance"""
    global _summarizer
    if _summarizer is None:
        print("Initializing MeetingSummarizer...")
        _summarizer = MeetingSummarizer()
        _summarizer.load_model()
        print("Model loaded successfully!")
    return _summarizer

def summarize_meeting(file_path: str) -> dict:
    """
    Summarize a meeting from audio/video file
    
    Args:
        file_path: Path to the meeting recording file
        
    Returns:
        dict with keys: summary, decisions, action_items
    """
    print(f"\n{'=' * 80}")
    print(f"Processing meeting file: {file_path}")
    print(f"{'=' * 80}\n")
    
    # Determine file type
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Prepare paths for intermediate files
    base_dir = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    audio_path = os.path.join(base_dir, f"{base_name}.wav")
    transcript_path = os.path.join(base_dir, f"{base_name}_transcript.txt")
    
    try:
        # Step 1: Convert to audio if needed (video files)
        if file_ext in ['.mp4', '.avi', '.mov', '.webm']:
            print("Step 1: Converting video to audio...")
            complete_pipeline.step1_convert_video_to_audio(file_path, audio_path)
        elif file_ext in ['.mp3', '.wav', '.m4a']:
            # If already audio, use it directly or convert to WAV
            if file_ext != '.wav':
                print("Step 1: Converting audio to WAV format...")
                complete_pipeline.step1_convert_video_to_audio(file_path, audio_path)
            else:
                audio_path = file_path
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Step 2: Transcribe audio
        print("\nStep 2: Transcribing audio...")
        complete_pipeline.step2_transcribe_audio(audio_path, transcript_path)
        
        # Step 3: Summarize transcript
        print("\nStep 3: Generating summary...")
        summarizer = get_summarizer()
        results = summarizer.summarize_meeting(transcript_path)
        
        print("\n✓ Summarization complete!")
        print(f"  Summary length: {len(results['summary'])} chars")
        print(f"  Decisions: {len(results['decisions'])}")
        print(f"  Action items: {len(results['action_items'])}")
        
        return results
        
    except Exception as e:
        print(f"\n✗ Error during summarization: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def test_summarizer():
    """Test function to verify the connector works"""
    print("Testing summarizer connector...")
    print("Note: This requires a test meeting file to work properly")

if __name__ == "__main__":
    test_summarizer()
