import axios from 'axios';

// Get the API URL from environment variables
const BACKEND_URL = (window.env && window.env.REACT_APP_API_URL) || process.env.REACT_APP_API_URL || "http://localhost:4455";

// Create axios instance with default config
const api = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: false,  // Changed to false to match CORS configuration
});

// Add request interceptor to add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/login', credentials),
  register: (userData) => api.post('/register', userData),
};

// Contract API
export const contractAPI = {
  analyze: (formData) => api.post('/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'text',
  }),
  getHistory: () => api.get('/history'),
  getReport: (wallet, filename) => api.get(`/report/${wallet}/${filename}`, {
    responseType: 'blob',
  }),
};

// Feedback API
export const feedbackAPI = {
  submitFeedback: (feedbackData) => api.post('/feedback', feedbackData),
};

export default api;
