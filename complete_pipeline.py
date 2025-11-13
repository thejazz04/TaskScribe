"""
Complete Meeting Summarizer Pipeline
Handles: Video -> Audio -> Transcription -> Summary/Decisions/Actions
"""
import os
import subprocess
import sys
from pathlib import Path
import config

# Configuration from config.py
VIDEO_FILE = config.VIDEO_FILE
AUDIO_FILE = config.AUDIO_FILE
TRANSCRIPTION_FILE = config.TRANSCRIPTION_FILE

def check_dependencies():
    """Check if required tools are installed"""
    print("Checking dependencies...")
    
    # Check ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✓ ffmpeg found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ ffmpeg not found. Please install ffmpeg.")
        return False
    
    # Check Python packages
    try:
        import whisper
        print("✓ whisper found")
    except ImportError:
        print("✗ whisper not found. Run: pip install openai-whisper")
        return False
    
    try:
        import transformers
        print("✓ transformers found")
    except ImportError:
        print("✗ transformers not found. Run: pip install transformers")
        return False
    
    return True

def step1_convert_video_to_audio(video_path: str, audio_path: str):
    """Convert video to audio using ffmpeg"""
    print("\n" + "=" * 80)
    print("STEP 1: Converting video to audio")
    print("=" * 80)
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    command = [
        "ffmpeg", "-i", video_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # Audio codec
        "-ar", "16000",  # Sample rate
        "-ac", "1",  # Mono channel
        "-y",  # Overwrite output
        audio_path
    ]
    
    print(f"Converting {video_path} -> {audio_path}")
    subprocess.run(command, check=True)
    print(f"✓ Audio extracted: {audio_path}")

def step2_transcribe_audio(audio_path: str, output_path: str):
    """Transcribe audio using Whisper"""
    print("\n" + "=" * 80)
    print("STEP 2: Transcribing audio")
    print("=" * 80)
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    import whisper
    
    # Use model from config (supports: tiny, base, small, medium, large)
    whisper_model = config.WHISPER_MODEL
    print(f"Loading Whisper model ({whisper_model})...")
    print("   Note: Large model provides best accuracy for long meetings")
    model = whisper.load_model(whisper_model)
    
    print(f"Transcribing {audio_path}...")
    print("   Whisper automatically handles long meetings by chunking audio")
    print("   This may take several minutes for long meetings...")
    
    # Prepare transcription parameters from config
    transcribe_kwargs = {
        "task": config.TRANSCRIPTION_TASK,
        "language": config.TRANSCRIPTION_LANGUAGE,
    }
    
    # Add chunk length if specified (for very long meetings)
    if config.WHISPER_CHUNK_LENGTH_S is not None:
        transcribe_kwargs["chunk_length_s"] = config.WHISPER_CHUNK_LENGTH_S
        print(f"   Using chunk length: {config.WHISPER_CHUNK_LENGTH_S} seconds")
    
    result = model.transcribe(audio_path, **transcribe_kwargs)
    
    transcript = result["text"]
    
    # Show segment info for long meetings
    if "segments" in result:
        print(f"   Processed {len(result['segments'])} audio segments")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(transcript)
    
    print(f"✓ Transcription saved: {output_path}")
    print(f"  Length: {len(transcript)} characters")

def step3_summarize_meeting(transcription_path: str):
    """Summarize meeting using LLM"""
    print("\n" + "=" * 80)
    print("STEP 3: Summarizing meeting")
    print("=" * 80)
    
    from meeting_summarizer_v2 import MeetingSummarizer
    
    summarizer = MeetingSummarizer()
    results = summarizer.summarize_meeting(transcription_path)
    summarizer.save_results(results, "meeting_summary.json", "meeting_summary.txt")
    
    print("✓ Meeting summarization complete!")

def main():
    """Run the complete pipeline"""
    print("=" * 80)
    print("MEETING SUMMARIZER - COMPLETE PIPELINE")
    print("=" * 80)
    
    # Check dependencies
    if not check_dependencies():
        print("\n✗ Missing dependencies. Please install them first.")
        sys.exit(1)
    
    try:
        # Step 1: Video to Audio
        if os.path.exists(VIDEO_FILE):
            step1_convert_video_to_audio(VIDEO_FILE, AUDIO_FILE)
        elif os.path.exists(AUDIO_FILE):
            print(f"\nSkipping Step 1: Audio file already exists ({AUDIO_FILE})")
        else:
            print(f"\n✗ Error: Neither {VIDEO_FILE} nor {AUDIO_FILE} found!")
            sys.exit(1)
        
        # Step 2: Audio to Transcription
        if not os.path.exists(TRANSCRIPTION_FILE):
            step2_transcribe_audio(AUDIO_FILE, TRANSCRIPTION_FILE)
        else:
            print(f"\nSkipping Step 2: Transcription already exists ({TRANSCRIPTION_FILE})")
        
        # Step 3: Transcription to Summary
        step3_summarize_meeting(TRANSCRIPTION_FILE)
        
        print("\n" + "=" * 80)
        print("✓ PIPELINE COMPLETE!")
        print("=" * 80)
        print("\nGenerated files:")
        print(f"  - {AUDIO_FILE}")
        print(f"  - {TRANSCRIPTION_FILE}")
        print(f"  - meeting_summary.json")
        print(f"  - meeting_summary.txt")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
