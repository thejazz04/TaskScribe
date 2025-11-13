# app_meeting.py - Streamlit Meeting Summarizer
import streamlit as st
import torch
import whisper
import subprocess
import os
import tempfile
from pathlib import Path
from meeting_summarizer_v2 import MeetingSummarizer
import json

st.set_page_config(page_title="Meeting Summarizer", layout="wide", page_icon="🎙️")
st.title("🎙️ Meeting Summarizer")
st.markdown("Upload a meeting video/audio file to get an AI-powered summary, decisions, and action items.")

# Configuration
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
WHISPER_MODEL = "small"  # Options: tiny, base, small, medium, large

# Sidebar
st.sidebar.markdown("### ⚙️ Settings")
st.sidebar.markdown(f"**Device:** {DEVICE}")
st.sidebar.markdown(f"**Whisper Model:** {WHISPER_MODEL}")
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Requirements")
st.sidebar.markdown("- FFmpeg installed")
st.sidebar.markdown("- Video/Audio file (mp4, mp3, wav, etc.)")

# Initialize session state
if "model_loaded" not in st.session_state:
    st.session_state.model_loaded = False
if "summarizer" not in st.session_state:
    st.session_state.summarizer = None
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "summary_results" not in st.session_state:
    st.session_state.summary_results = None

@st.cache_resource(show_spinner=False)
def load_whisper_model(model_size: str = "small"):
    """Load Whisper model"""
    return whisper.load_model(model_size)

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def convert_to_audio(input_path: str, output_path: str):
    """Convert video/audio to WAV format using ffmpeg"""
    command = [
        "ffmpeg", "-i", input_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # Audio codec
        "-ar", "16000",  # Sample rate
        "-ac", "1",  # Mono channel
        "-y",  # Overwrite
        output_path
    ]
    subprocess.run(command, check=True, capture_output=True)

def transcribe_audio(audio_path: str, model_size: str = "small") -> str:
    """Transcribe audio using Whisper"""
    model = load_whisper_model(model_size)
    result = model.transcribe(audio_path, task="transcribe", language="en")
    return result["text"]

# Main UI
tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "📄 Transcript", "📊 Summary"])

with tab1:
    st.header("Upload Meeting File")
    
    # Check FFmpeg
    if not check_ffmpeg():
        st.error("❌ FFmpeg not found! Please install FFmpeg first.")
        st.markdown("""
        **Install FFmpeg:**
        - Windows: `choco install ffmpeg` or download from https://ffmpeg.org
        - Linux: `sudo apt install ffmpeg`
        - macOS: `brew install ffmpeg`
        """)
        st.stop()
    else:
        st.success("✓ FFmpeg found")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a video or audio file",
        type=["mp4", "mp3", "wav", "m4a", "avi", "mov", "webm"],
        help="Supported formats: MP4, MP3, WAV, M4A, AVI, MOV, WebM"
    )
    
    if uploaded_file is not None:
        # Show file info
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.info(f"📁 File: {uploaded_file.name} ({file_size_mb:.2f} MB)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎤 Transcribe Audio", type="primary", use_container_width=True):
                with st.spinner("Processing audio..."):
                    try:
                        # Save uploaded file to temp location
                        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_input:
                            tmp_input.write(uploaded_file.getvalue())
                            tmp_input_path = tmp_input.name
                        
                        # Convert to WAV
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                            tmp_audio_path = tmp_audio.name
                        
                        st.info("Converting to audio format...")
                        convert_to_audio(tmp_input_path, tmp_audio_path)
                        
                        # Transcribe
                        st.info("Transcribing with Whisper (this may take a few minutes)...")
                        transcript = transcribe_audio(tmp_audio_path, WHISPER_MODEL)
                        
                        # Store in session state
                        st.session_state.transcript = transcript
                        
                        # Cleanup
                        os.unlink(tmp_input_path)
                        os.unlink(tmp_audio_path)
                        
                        st.success("✅ Transcription complete!")
                        
                    except Exception as e:
                        st.error(f"Error during transcription: {e}")
                        import traceback
                        st.code(traceback.format_exc())
        
        with col2:
            if st.button("🤖 Load Summarizer Model", use_container_width=True):
                with st.spinner("Loading LLM model (this may take a few minutes)..."):
                    try:
                        summarizer = MeetingSummarizer()
                        summarizer.load_model()
                        st.session_state.summarizer = summarizer
                        st.session_state.model_loaded = True
                        st.success("✅ Model loaded!")
                    except Exception as e:
                        st.error(f"Error loading model: {e}")
                        import traceback
                        st.code(traceback.format_exc())
        
        # Generate summary
        if st.session_state.transcript and st.session_state.model_loaded:
            st.markdown("---")
            if st.button("📝 Generate Summary", type="primary", use_container_width=True):
                with st.spinner("Generating summary..."):
                    try:
                        # Save transcript temporarily
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_transcript:
                            tmp_transcript.write(st.session_state.transcript)
                            tmp_transcript_path = tmp_transcript.name
                        
                        # Generate summary
                        results = st.session_state.summarizer.summarize_meeting(tmp_transcript_path)
                        st.session_state.summary_results = results
                        
                        # Cleanup
                        os.unlink(tmp_transcript_path)
                        
                        st.success("✅ Summary generated! Check the 'Summary' tab.")
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
                        import traceback
                        with st.expander("Show error details"):
                            st.code(traceback.format_exc())
        elif not st.session_state.transcript:
            st.info("Complete transcription first.")
        elif not st.session_state.model_loaded:
            st.info("Load the model first.")

with tab2:
    st.header("📄 Meeting Transcript")
    
    if st.session_state.transcript:
        # Simple transcript display
        st.text_area(
            "Transcript",
            value=st.session_state.transcript,
            height=600,
            label_visibility="visible"
        )
        
        # Download button
        st.download_button(
            label="📥 Download Transcript",
            data=st.session_state.transcript,
            file_name="meeting_transcript.txt",
            mime="text/plain"
        )
    else:
        st.info("No transcript available. Go to 'Upload & Process' tab to transcribe audio.")

with tab3:
    st.header("📊 Meeting Summary")
    
    if st.session_state.summary_results:
        results = st.session_state.summary_results
        
        st.success("✅ Summary generated successfully!")
        st.markdown("---")
        
        # Summary section - Simple display
        st.markdown("### Summary")
        st.write(results["summary"])
        st.markdown("---")
        
        # Decisions section
        st.markdown("### Decisions")
        if results["decisions"]:
            for i, decision in enumerate(results["decisions"], 1):
                st.write(f"{i}. {decision}")
        else:
            st.write("No decisions recorded.")
        st.markdown("---")
        
        # Action items section
        st.markdown("### Action Items")
        if results["action_items"]:
            for i, item in enumerate(results["action_items"], 1):
                task = item.get('task', 'N/A')
                owner = item.get('owner') or 'Not assigned'
                due_date = item.get('due_date') or 'Not specified'
                notes = item.get('notes') or ''
                
                st.write(f"**{i}. {task}**")
                st.write(f"   Owner: {owner}")
                st.write(f"   Due Date: {due_date}")
                if notes:
                    st.write(f"   Notes: {notes}")
                st.write("")
        else:
            st.write("No action items recorded.")
        
        st.markdown("---")
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            json_str = json.dumps(results, indent=2, ensure_ascii=False)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name="meeting_summary.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            txt_content = f"""MEETING SUMMARY
{'=' * 80}

SUMMARY:
{'-' * 80}
{results['summary']}

DECISIONS:
{'-' * 80}
"""
            if results["decisions"]:
                for i, decision in enumerate(results["decisions"], 1):
                    txt_content += f"{i}. {decision}\n"
            else:
                txt_content += "No decisions recorded.\n"
            
            txt_content += f"""
ACTION ITEMS:
{'-' * 80}
"""
            if results["action_items"]:
                for i, item in enumerate(results["action_items"], 1):
                    txt_content += f"\n{i}. {item.get('task', 'N/A')}\n"
                    txt_content += f"   Owner: {item.get('owner') or 'Not assigned'}\n"
                    txt_content += f"   Due Date: {item.get('due_date') or 'Not specified'}\n"
                    if item.get('notes'):
                        txt_content += f"   Notes: {item.get('notes')}\n"
            else:
                txt_content += "No action items recorded.\n"
            
            st.download_button(
                label="Download TXT",
                data=txt_content,
                file_name="meeting_summary.txt",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("No summary available. Complete transcription and model loading, then generate summary.")

# Footer
st.markdown("---")
st.markdown("**💡 Tip:** For best results, use clear audio with minimal background noise.")

