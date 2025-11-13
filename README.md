# Meeting Summarizer - AI-Powered Meeting Analysis

> Automatically convert meeting recordings into structured summaries, decisions, and action items.

---

## 🚀 Quick Start

### 1. Install FFmpeg
```bash
# Windows
choco install ffmpeg

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### 2. Setup Python
```bash
cd NLP
.\llm_env\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Run
```bash
# Place your video as meeting.mp4
python complete_pipeline.py
```

**Done!** Check `meeting_summary.txt`

---

## 📁 Project Structure

```
NLP/
├── complete_pipeline.py         # Main script - run this
├── meeting_summarizer_v2.py     # AI summarization engine
├── config.py                    # All settings
├── test_setup.py                # Verify installation
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

---

## 🏗️ How It Works

```
┌─────────────┐
│ meeting.mp4 │  Your video
└──────┬──────┘
       │
       ▼ FFmpeg (30 sec)
┌─────────────┐
│ meeting.wav │  Audio extracted
└──────┬──────┘
       │
       ▼ Whisper (2-5 min)
┌──────────────────┐
│ transcription.txt│  Full transcript
└────────┬─────────┘
         │
         ▼ LLaMA 3.2 (1-3 min)
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│ .json   │ │ .txt    │  Structured summary
└─────────┘ └─────────┘
```

**Total Time:** 3-10 minutes for 30-min meeting

---

## 📊 Output Example

**Input:** 30-minute team meeting

**Output:**
```
SUMMARY:
The SEC team meeting covered organizational changes, including Alan 
stepping in as acting manager. The team discussed MR rate improvements 
through weekly refinement meetings. Key topics included FedRAMP 
compliance and talent assessment timeline.

DECISIONS:
1. Alan will serve as acting full stack manager for security policies
2. Data science section will include model ops and anti-abuse stages
3. Team will add work anniversaries to meeting template

ACTION ITEMS:
1. Report back on frame abuse improvements
   Owner: Neil | Due: End of quarter

2. Review development vision feedback
   Owner: Team | Due: Next week
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Change models
LLM_MODEL = "meta-llama/Llama-3.2-3B-Instruct"  # or 1B for faster
WHISPER_MODEL = "large"  # tiny, base, small, medium, large
# Large model recommended for best accuracy, especially for long meetings
# Whisper automatically chunks long audio (handles meetings of any length)

# Adjust processing
LLM_TEMPERATURE = 0.3  # Lower = more focused
MAX_TRANSCRIPT_LENGTH = 4000
```

---

## 🔧 System Architecture

### Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Video Processing | FFmpeg | Extract audio (16kHz, mono) |
| Speech-to-Text | OpenAI Whisper | Transcribe audio |
| AI Summarization | LLaMA 3.2 3B | Extract structured info |
| Acceleration | CUDA + 4-bit quantization | Fast GPU processing |

### Data Flow

```
Video → Audio → Transcript → AI Processing → Structured Output
                                    ↓
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
                Summary         Decisions      Action Items
                (4-6 sent)      (list)         (task/owner/date)
```

### AI Processing Pipeline

```
Transcript
    │
    ├─▶ Prompt 1: Summary → LLaMA → Summary (4-6 sentences)
    │
    ├─▶ Prompt 2: Decisions → LLaMA → Decisions (array)
    │
    └─▶ Prompt 3: Actions → LLaMA → Action Items (structured)
                                        ↓
                            {task, owner, due_date, notes}
```

---

## 💻 System Requirements

### Minimum (CPU)
- Python 3.8+
- 8 GB RAM
- 10 GB disk space

### Recommended (GPU)
- NVIDIA GPU with 6+ GB VRAM
- CUDA installed
- 8 GB RAM

---

## 📈 Performance

| Configuration | Time (30-min meeting) | Accuracy |
|--------------|----------------------|----------|
| CPU + Small Models | ~10 min | Good |
| GPU + Balanced | ~3 min | Very Good ⭐ |
| GPU + Large Models | ~5 min | Excellent |

---

## 🐛 Troubleshooting

### "ffmpeg not found"
```bash
# Install FFmpeg (see Quick Start section)
ffmpeg -version  # Verify installation
```

### "CUDA out of memory"
```python
# Edit config.py - use smaller model
LLM_MODEL = "meta-llama/Llama-3.2-1B-Instruct"
```

### "No module named 'whisper'"
```bash
pip install openai-whisper
```

### Poor summary quality
- Use larger Whisper model: `WHISPER_MODEL = "medium"`
- Check audio quality in original recording
- Ensure speakers mention decisions/actions explicitly

---

## 🎯 Usage Tips

### For Best Results:
1. **Clear audio** - Good microphone, minimal background noise
2. **Structured meetings** - Explicitly state decisions: "We decided to..."
3. **Clear assignments** - "John will do X by Friday"
4. **Use names** - Better owner identification

### Customization:
```python
# Edit config.py to change prompts
SUMMARY_PROMPT_TEMPLATE = """
Your custom prompt here...
"""
```

---

## 📊 Technical Details

### Models Used
- **Whisper Large**: 1550M parameters, ~3 GB (default, best accuracy)
- **LLaMA 3.2 3B**: 3B parameters, ~6 GB (4-bit quantized)

### Long Meeting Support
**Yes, Whisper Large can handle meetings of any length!**

- **Automatic Chunking**: Whisper automatically splits long audio into 30-second segments
- **No Length Limit**: Can process meetings from minutes to hours
- **Better Accuracy**: Large model provides superior transcription quality for:
  - Long conversations
  - Multiple speakers
  - Background noise
  - Technical terminology
- **Processing Time**: ~1-2 minutes per 10 minutes of audio (on GPU)
- **Memory Efficient**: Processes chunks sequentially, doesn't load entire audio into memory

### Processing Steps
1. **Video → Audio**: FFmpeg extracts 16kHz mono WAV
2. **Audio → Text**: Whisper transcribes with timestamps
3. **Text → Summary**: LLaMA extracts with 3 separate prompts
4. **JSON Parsing**: Multiple fallback mechanisms
5. **Output**: Both JSON (structured) and TXT (readable)

### Key Features
- ✅ Whisper Large model for best transcription accuracy
- ✅ Automatic handling of long meetings (any length)
- ✅ 4-bit quantization for memory efficiency
- ✅ Separate prompts for better extraction
- ✅ Multiple JSON parsing fallbacks
- ✅ Temperature control (0.3) for focused output
- ✅ Robust error handling

---

## 🔄 Workflow Integration

### Current
```
Meeting Recording → Meeting Summarizer → Manual Distribution
```

### Future
```
Meeting Recording → Meeting Summarizer → Auto Distribution
                                       ↓
                    ┌──────────────────┼──────────────────┐
                    ↓                  ↓                  ↓
                  Email              Slack              Jira
                (Summary)         (Decisions)      (Action Items)
```

---

## 📝 Output Formats

### JSON (meeting_summary.json)
```json
{
  "summary": "Concise meeting overview...",
  "decisions": [
    "Decision 1",
    "Decision 2"
  ],
  "action_items": [
    {
      "task": "Task description",
      "owner": "Person name",
      "due_date": "Deadline",
      "notes": null
    }
  ]
}
```

### TXT (meeting_summary.txt)
Human-readable format with clear sections.

---

## 🚀 Advanced Usage

### Run Individual Steps
```bash
# Summarize existing transcript (if you already have transcription.txt)
python meeting_summarizer_v2.py

# Or use complete_pipeline.py which handles everything
python complete_pipeline.py
```

### Test Setup
```bash
python test_setup.py
```

### Custom Configuration
```python
# config.py
VIDEO_FILE = "your_video.mp4"
LLM_MODEL = "meta-llama/Llama-3.2-1B-Instruct"  # Faster
WHISPER_MODEL = "tiny"  # Faster
```

---

## 📈 Roadmap

### Current ✅
- Video to audio conversion
- Audio transcription
- Summary extraction
- Decision extraction
- Action item extraction

### Planned 🚧
- Speaker diarization (who said what)
- Web interface
- Real-time recording
- Multi-language support
- Email/Slack integration

---

## 🤝 Contributing

Improvements welcome:
- Better prompts for extraction
- Support for more languages
- Additional output formats
- Performance optimizations

---

## 📄 License

MIT License - Free to use and modify

---

## 🙏 Built With

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [LLaMA 3.2](https://huggingface.co/meta-llama) - Language understanding
- [Transformers](https://huggingface.co/transformers) - ML framework
- [FFmpeg](https://ffmpeg.org/) - Media processing

---

## 📞 Quick Reference

```bash
# Setup (one-time)
pip install -r requirements.txt

# Test
python test_setup.py

# Run
python complete_pipeline.py

# Customize
# Edit config.py
```

---

**Made with ❤️ for better meetings**

---

## 📊 Model Accuracy & Troubleshooting

For detailed information about:
- Whisper Large model accuracy (WER: 5-15%)
- Why decisions/action items might be empty
- How to improve extraction results
- Troubleshooting guide

See **[MODEL_ACCURACY.md](MODEL_ACCURACY.md)**
