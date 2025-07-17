import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// You can add interceptors here later for handling auth tokens or errors
// apiClient.interceptors.request.use(...)

export default apiClient;