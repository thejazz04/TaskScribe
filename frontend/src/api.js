import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadMeeting = async (file, title, userName) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('userName', userName || 'Anonymous');

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getMeetings = async () => {
  const response = await api.get('/meetings');
  return response.data.meetings;
};

export const getMeeting = async (meetingId) => {
  const response = await api.get(`/meeting/${meetingId}`);
  return response.data.meeting;
};

export const downloadSummary = (meetingId) => {
  window.open(`${API_URL}/api/meeting/${meetingId}/download`, '_blank');
};

export const deleteMeeting = async (meetingId) => {
  const response = await api.delete(`/meeting/${meetingId}`);
  return response.data;
};

// Live Meeting APIs
export const createRoom = async (hostName, title) => {
  const response = await api.post('/room/create', { hostName, title });
  return response.data;
};

export const getRoomInfo = async (roomId) => {
  const response = await api.get(`/room/${roomId}`);
  return response.data.room;
};

export default api;
