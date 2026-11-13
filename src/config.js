// Where the backend API lives. In order:
// 1. The backend serves this page itself (standalone package): it sets
//    window.EXCEL_VISUALISER_API_URL to the page's own address.
// 2. REACT_APP_API_URL given at build or start time.
// 3. Port 5001 on the host this page was loaded from. On this computer that
//    is localhost; in shared mode it is the computer running the app.
const sameHostApi = () => {
  const { protocol, hostname } = window.location;
  if (!hostname) return 'http://localhost:5001';
  return `${protocol === 'https:' ? 'https:' : 'http:'}//${hostname}:5001`;
};

const API_BASE_URL = (
  window.EXCEL_VISUALISER_API_URL || process.env.REACT_APP_API_URL || sameHostApi()
).replace(/\/+$/, '');

export default API_BASE_URL;
