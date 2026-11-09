// Override at build/start time with REACT_APP_API_URL when the backend is not on localhost.
const API_BASE_URL = (process.env.REACT_APP_API_URL || 'http://localhost:5001').replace(/\/+$/, '');
export default API_BASE_URL;
