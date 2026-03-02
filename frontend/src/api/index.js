import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

export const optimizeApi = {
    getLocations: () => api.get('/locations'),
    createJob: (city, locations) => api.post('/optimize', { city, locations }),
    getJobStatus: (jobId) => api.get(`/status/${jobId}`),
};
