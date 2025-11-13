"""
Flask Backend for Meeting Summarizer
Handles file uploads, summarization, MongoDB storage, and live meetings
"""
import os
import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import summarize_connector

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/meeting_summarizer")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mp4', 'mp3', 'wav', 'webm', 'm4a', 'avi', 'mov'}

# Initialize MongoDB
mongo = PyMongo(app)

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Server is running"})

@app.route('/api/upload', methods=['POST'])
def upload_meeting():
    """
    Upload meeting file, run summarization, and save to MongoDB
    Expected form data:
    - file: meeting recording file
    - title: meeting title
    """
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        title = request.form.get('title', 'Untitled Meeting')
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
        
        # Generate unique meeting ID
        meeting_id = str(uuid.uuid4())
        
        # Save file
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        saved_filename = f"{meeting_id}.{file_extension}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_filename)
        file.save(file_path)
        
        print(f"File saved: {file_path}")
        
        # Run summarization
        print(f"Starting summarization for: {title}")
        summary_result = summarize_connector.summarize_meeting(file_path)
        
        # Get user name from form
        user_name = request.form.get('userName', 'Anonymous')
        
        # Prepare meeting document
        meeting_doc = {
            "meetingId": meeting_id,
            "userName": user_name,
            "title": title,
            "date": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "summary": summary_result.get("summary", ""),
            "decisions": summary_result.get("decisions", []),
            "actionItems": summary_result.get("action_items", []),
            "filePath": file_path,
            "fileName": filename
        }
        
        # Save to MongoDB
        mongo.db.meetings.insert_one(meeting_doc)
        
        print(f"Meeting saved to database: {meeting_id}")
        
        # Return response (remove _id for JSON serialization)
        meeting_doc.pop('_id', None)
        
        return jsonify({
            "message": "Meeting uploaded and summarized successfully",
            "meeting": meeting_doc
        }), 201
        
    except Exception as e:
        print(f"Error in upload_meeting: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/meetings', methods=['GET'])
def get_meetings():
    """Get all meetings"""
    try:
        meetings = list(mongo.db.meetings.find({}, {'_id': 0}).sort("date", -1))
        return jsonify({"meetings": meetings}), 200
    except Exception as e:
        print(f"Error in get_meetings: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/meeting/<meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    """Get a specific meeting by ID"""
    try:
        meeting = mongo.db.meetings.find_one({"meetingId": meeting_id}, {'_id': 0})
        
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404
        
        return jsonify({"meeting": meeting}), 200
    except Exception as e:
        print(f"Error in get_meeting: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/meeting/<meeting_id>/download', methods=['GET'])
def download_summary(meeting_id):
    """Download meeting summary as text file"""
    try:
        meeting = mongo.db.meetings.find_one({"meetingId": meeting_id, "userId": request.user_id}, {'_id': 0})
        
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404
        
        # Generate text content
        content = f"""{'=' * 80}
MEETING SUMMARY
{'=' * 80}

Title: {meeting.get('title', 'N/A')}
Date: {meeting.get('date', 'N/A')}

SUMMARY:
{'-' * 80}
{meeting.get('summary', 'No summary available')}

DECISIONS:
{'-' * 80}
"""
        decisions = meeting.get('decisions', [])
        if decisions:
            for i, decision in enumerate(decisions, 1):
                content += f"{i}. {decision}\n"
        else:
            content += "No decisions recorded.\n"
        
        content += f"\nACTION ITEMS:\n{'-' * 80}\n"
        action_items = meeting.get('actionItems', [])
        if action_items:
            for i, item in enumerate(action_items, 1):
                content += f"\n{i}. {item.get('task', 'N/A')}\n"
                content += f"   Owner: {item.get('owner') or 'Not assigned'}\n"
                content += f"   Due Date: {item.get('due_date') or 'Not specified'}\n"
                if item.get('notes'):
                    content += f"   Notes: {item.get('notes')}\n"
        else:
            content += "No action items recorded.\n"
        
        # Save to temporary file
        temp_filename = f"{meeting_id}_summary.txt"
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], temp_filename)
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return send_file(temp_path, as_attachment=True, download_name=f"{meeting.get('title', 'meeting')}_summary.txt")
        
    except Exception as e:
        print(f"Error in download_summary: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/meeting/<meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    """Delete a meeting"""
    try:
        meeting = mongo.db.meetings.find_one({"meetingId": meeting_id})
        
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404
        
        # Delete file if exists
        file_path = meeting.get('filePath')
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        mongo.db.meetings.delete_one({"meetingId": meeting_id})
        
        return jsonify({"message": "Meeting deleted successfully"}), 200
        
    except Exception as e:
        print(f"Error in delete_meeting: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Live Meeting Management
active_rooms = {}  # {room_id: {participants: [], host: user_id, recording: bool}}

@app.route('/api/room/create', methods=['POST'])
def create_room():
    """Create a new meeting room"""
    try:
        data = request.get_json()
        host_name = data.get('hostName', 'Anonymous')
        room_title = data.get('title', 'Untitled Meeting')
        
        room_id = str(uuid.uuid4())[:8]  # Short room ID
        
        room_doc = {
            "roomId": room_id,
            "title": room_title,
            "hostName": host_name,
            "createdAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "status": "active",
            "participants": []
        }
        
        mongo.db.rooms.insert_one(room_doc)
        active_rooms[room_id] = {
            "participants": [],
            "host": host_name,
            "recording": False,
            "title": room_title
        }
        
        # Remove _id for JSON serialization
        room_doc.pop('_id', None)
        
        return jsonify({
            "message": "Room created successfully",
            "roomId": room_id,
            "room": room_doc
        }), 201
        
    except Exception as e:
        print(f"Error in create_room: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/room/<room_id>', methods=['GET'])
def get_room(room_id):
    """Get room details"""
    try:
        room = mongo.db.rooms.find_one({"roomId": room_id}, {'_id': 0})
        
        if not room:
            return jsonify({"error": "Room not found"}), 404
        
        # Add live participant count
        if room_id in active_rooms:
            room['participantCount'] = len(active_rooms[room_id]['participants'])
        else:
            room['participantCount'] = 0
        
        return jsonify({"room": room}), 200
        
    except Exception as e:
        print(f"Error in get_room: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Socket.IO Events for WebRTC Signaling
@socketio.on('join-room')
def handle_join_room(data):
    """User joins a meeting room"""
    room_id = data.get('roomId')
    user_name = data.get('userName', 'Anonymous')
    user_id = data.get('userId', str(uuid.uuid4()))
    
    join_room(room_id)
    
    if room_id not in active_rooms:
        active_rooms[room_id] = {
            "participants": [],
            "host": user_name,
            "recording": False,
            "title": "Meeting"
        }
    
    participant = {
        "userId": user_id,
        "userName": user_name,
        "joinedAt": datetime.now(timezone.utc).isoformat()
    }
    
    active_rooms[room_id]['participants'].append(participant)
    
    # Notify others in the room
    emit('user-joined', {
        "userId": user_id,
        "userName": user_name,
        "participantCount": len(active_rooms[room_id]['participants'])
    }, room=room_id, skip_sid=request.sid)
    
    # Send current participants to the new user
    emit('room-users', {
        "participants": active_rooms[room_id]['participants']
    })
    
    print(f"User {user_name} joined room {room_id}")

@socketio.on('leave-room')
def handle_leave_room(data):
    """User leaves a meeting room"""
    room_id = data.get('roomId')
    user_id = data.get('userId')
    
    leave_room(room_id)
    
    if room_id in active_rooms:
        active_rooms[room_id]['participants'] = [
            p for p in active_rooms[room_id]['participants'] 
            if p['userId'] != user_id
        ]
        
        emit('user-left', {
            "userId": user_id,
            "participantCount": len(active_rooms[room_id]['participants'])
        }, room=room_id)
        
        print(f"User {user_id} left room {room_id}")

@socketio.on('webrtc-offer')
def handle_webrtc_offer(data):
    """Forward WebRTC offer to specific peer"""
    target_id = data.get('targetId')
    offer = data.get('offer')
    sender_id = data.get('senderId')
    
    emit('webrtc-offer', {
        "offer": offer,
        "senderId": sender_id
    }, room=target_id)

@socketio.on('webrtc-answer')
def handle_webrtc_answer(data):
    """Forward WebRTC answer to specific peer"""
    target_id = data.get('targetId')
    answer = data.get('answer')
    sender_id = data.get('senderId')
    
    emit('webrtc-answer', {
        "answer": answer,
        "senderId": sender_id
    }, room=target_id)

@socketio.on('webrtc-ice-candidate')
def handle_ice_candidate(data):
    """Forward ICE candidate to specific peer"""
    target_id = data.get('targetId')
    candidate = data.get('candidate')
    sender_id = data.get('senderId')
    
    emit('webrtc-ice-candidate', {
        "candidate": candidate,
        "senderId": sender_id
    }, room=target_id)

@socketio.on('start-recording')
def handle_start_recording(data):
    """Start recording the meeting"""
    room_id = data.get('roomId')
    
    if room_id in active_rooms:
        active_rooms[room_id]['recording'] = True
        emit('recording-started', {}, room=room_id)
        print(f"Recording started in room {room_id}")

@socketio.on('stop-recording')
def handle_stop_recording(data):
    """Stop recording the meeting"""
    room_id = data.get('roomId')
    
    if room_id in active_rooms:
        active_rooms[room_id]['recording'] = False
        emit('recording-stopped', {}, room=room_id)
        print(f"Recording stopped in room {room_id}")

if __name__ == '__main__':
    print("Starting Flask server with Socket.IO...")
    print(f"MongoDB URI: {app.config['MONGO_URI']}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
