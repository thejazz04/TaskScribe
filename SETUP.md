# Meeting Summarizer - Setup Guide

## 🎯 Features

- ✅ User Authentication (JWT)
- ✅ Upload & Summarize Meetings
- ✅ **NEW!** Live Meeting Recording
- ✅ AI-Powered Summaries (Whisper + Llama)
- ✅ Extract Decisions & Action Items
- ✅ MongoDB Atlas Storage

## Prerequisites

- Python 3.8+
- Node.js 18+
- ffmpeg

## Installation

### 1. Install ffmpeg

```bash
choco install ffmpeg
```

### 2. Backend Setup

```bash
cd backend
pip install PyJWT bcrypt  # Auth dependencies
install_dependencies.bat  # AI dependencies (~5GB)
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Start Backend
```bash
cd backend
python server.py
```
Runs on http://localhost:5000

### Start Frontend
```bash
cd frontend
npm run dev
```
Runs on http://localhost:3000

## Configuration

### Backend (.env)
```env
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/meeting_summarizer
JWT_SECRET_KEY=your-secret-key-change-in-production
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:5000
```

### AI Model (config.py)
```python
WHISPER_MODEL = "medium"  # medium/large
LLM_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
```

## Usage

1. **Sign Up** - Create account at http://localhost:3000/signup
2. **Login** - Sign in with your credentials
3. **Record** - Click "Record" to record live meeting
4. **Upload** - Or upload existing audio/video file
5. **View** - Check dashboard for all summaries

## API Endpoints

### Auth
- `POST /api/auth/signup` - Register user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Meetings (Protected)
- `POST /api/upload` - Upload meeting
- `GET /api/meetings` - List user's meetings
- `GET /api/meeting/<id>` - Get meeting details
- `GET /api/meeting/<id>/download` - Download summary
- `DELETE /api/meeting/<id>` - Delete meeting

## Troubleshooting

**"No module named 'torch'"**
```bash
cd backend
pip install torch transformers openai-whisper accelerate
```

**"No module named 'jwt'"**
```bash
pip install PyJWT bcrypt
```

**"MongoDB connection failed"**
- Check MONGO_URI in backend/.env
- Ensure MongoDB Atlas cluster is running

## Project Structure

```
NLP/
├── backend/
│   ├── server.py          # Flask API
│   ├── auth.py            # JWT authentication
│   ├── summarize_connector.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Signup.jsx
│   │   │   ├── Record.jsx  # NEW!
│   │   │   ├── Upload.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── MeetingDetail.jsx
│   │   └── api.js
│   └── package.json
└── SETUP.md
```
