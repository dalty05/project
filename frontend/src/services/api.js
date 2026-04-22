import axios from "axios";

// Create a custom axios instance
const api = axios.create({
  baseURL: "https://daltyo5.pythonanywhere.com",
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor: Runs BEFORE every request is sent out
api.interceptors.request.use(
  (config) => {
    // Get the access token from localStorage
    const token = localStorage.getItem("token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor: Runs AFTER every response is received
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Check if the backend sent an error message or a JWT 'msg'
    const backendMessage = error.response?.data?.message || error.response?.data?.msg;
    
    if (backendMessage) {
      error.response.data.message = backendMessage; // Unify everything to .message
    }

    // Auto-logout if token is invalid or expired
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    
    return Promise.reject(error);
  }
);

export default api;
