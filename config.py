"""
Configuration file for Meeting Summarizer
Edit these settings to customize the behavior
"""

# ============================================================================
# FILE PATHS
# ============================================================================

# Input files
VIDEO_FILE = "meeting.mp4"              # Your meeting video file
AUDIO_FILE = "meeting.wav"              # Extracted audio (auto-generated)
TRANSCRIPTION_FILE = "transcription.txt"  # Transcript (auto-generated)

# Output files
OUTPUT_JSON = "meeting_summary.json"    # Structured JSON output
OUTPUT_TXT = "meeting_summary.txt"      # Human-readable summary

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# LLM Model for summarization
# Options:
#   - "meta-llama/Llama-3.2-1B-Instruct"  (Fast, less accurate, ~2GB)
#   - "meta-llama/Llama-3.2-3B-Instruct"  (Balanced, recommended, ~6GB)
#   - "google/flan-t5-large"              (Alternative, ~3GB)
LLM_MODEL = "meta-llama/Llama-3.2-3B-Instruct"

# Whisper model for transcription
# Options: "tiny", "base", "small", "medium", "large"
# Larger = more accurate but slower
# "large" recommended for best accuracy, especially for long meetings
WHISPER_MODEL = "large"

# ============================================================================
# PROCESSING SETTINGS
# ============================================================================

# Audio conversion settings
AUDIO_SAMPLE_RATE = 16000  # Hz (16kHz is optimal for speech)
AUDIO_CHANNELS = 1         # Mono audio

# Transcription settings
TRANSCRIPTION_LANGUAGE = "en"  # Language code (en, es, fr, etc.)
TRANSCRIPTION_TASK = "transcribe"  # "transcribe" or "translate"

# Long meeting support
# Whisper processes audio in chunks. For very long meetings (>2 hours),
# you can adjust chunk_length_s. Default is 30 seconds per chunk.
# Set to None to use Whisper's default chunking (handles any length)
WHISPER_CHUNK_LENGTH_S = None  # None = auto (recommended), or set to 30, 60, etc.

# LLM generation settings
LLM_TEMPERATURE = 0.3      # Lower = more focused, Higher = more creative
LLM_MAX_TOKENS = 512       # Maximum tokens to generate
LLM_TOP_P = 0.9           # Nucleus sampling parameter

# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

# Summary prompt template
SUMMARY_PROMPT_TEMPLATE = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a professional meeting assistant. Create a concise executive summary of the meeting.<|eot_id|>

<|start_header_id|>user<|end_header_id|>
Read the following meeting transcript and write a concise summary in 4-6 sentences. Focus on:
- Main topics discussed
- Key outcomes
- Overall purpose of the meeting

Do NOT copy the transcript verbatim. Synthesize the information.

TRANSCRIPT:
{transcript}

SUMMARY:<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>"""

# Decisions prompt template
DECISIONS_PROMPT_TEMPLATE = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a meeting assistant that extracts decisions from meeting transcripts.<|eot_id|>

<|start_header_id|>user<|end_header_id|>
Read the meeting transcript and extract all DECISIONS that were made. 
A decision is a conclusion or agreement reached by the team.

Return ONLY a JSON array of decision strings. If no decisions, return empty array [].

TRANSCRIPT:
{transcript}

DECISIONS (JSON array only):<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>"""

# Action items prompt template
ACTION_ITEMS_PROMPT_TEMPLATE = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a meeting assistant that extracts action items from meetings.<|eot_id|>

<|start_header_id|>user<|end_header_id|>
Read the meeting transcript and extract all ACTION ITEMS.
An action item is a task that someone needs to complete.

Return ONLY a JSON array of objects with this structure:
[
  {{
    "task": "description of the task",
    "owner": "person responsible (or null if not mentioned)",
    "due_date": "deadline (or null if not mentioned)",
    "notes": "additional context (or null)"
  }}
]

If no action items found, return empty array [].

TRANSCRIPT:
{transcript}

ACTION ITEMS (JSON array only):<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>"""

# ============================================================================
# ADVANCED SETTINGS
# ============================================================================

# Enable 4-bit quantization (saves memory, requires bitsandbytes)
USE_4BIT_QUANTIZATION = True

# Maximum transcript length to process (characters)
MAX_TRANSCRIPT_LENGTH = 4000

# Chunk size for long transcripts
CHUNK_SIZE = 3500

# Device preference ("cuda", "cpu", or "auto")
DEVICE = "auto"  # "auto" will use CUDA if available, else CPU

# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

# JSON output formatting
JSON_INDENT = 2
JSON_ENSURE_ASCII = False

# Text output formatting
TXT_LINE_WIDTH = 80
TXT_SECTION_SEPARATOR = "=" * 80
TXT_SUBSECTION_SEPARATOR = "-" * 80

# ============================================================================
# LOGGING
# ============================================================================

# Enable verbose logging
VERBOSE = True

# Log file (None to disable file logging)
LOG_FILE = None  # or "meeting_summarizer.log"

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration settings"""
    import os
    
    errors = []
    
    # Check Whisper model
    valid_whisper = ["tiny", "base", "small", "medium", "large"]
    if WHISPER_MODEL not in valid_whisper:
        errors.append(f"Invalid WHISPER_MODEL: {WHISPER_MODEL}. Must be one of {valid_whisper}")
    
    # Check temperature
    if not 0 <= LLM_TEMPERATURE <= 2:
        errors.append(f"LLM_TEMPERATURE must be between 0 and 2, got {LLM_TEMPERATURE}")
    
    # Check device
    valid_devices = ["cuda", "cpu", "auto"]
    if DEVICE not in valid_devices:
        errors.append(f"Invalid DEVICE: {DEVICE}. Must be one of {valid_devices}")
    
    if errors:
        print("Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

# Validate on import
if __name__ != "__main__":
    validate_config()
