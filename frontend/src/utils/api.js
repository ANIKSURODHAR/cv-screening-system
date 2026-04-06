/**
 * API utility — Axios instance with JWT token handling.
 * Auto-attaches Bearer token, auto-refreshes on 401.
 */
import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Don't set Content-Type for FormData (file uploads)
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  return config;
});

// Auto-refresh token on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) throw new Error("No refresh token");

        const res = await axios.post(`${API_BASE}/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        localStorage.setItem("access_token", res.data.access);
        if (res.data.refresh) {
          localStorage.setItem("refresh_token", res.data.refresh);
        }

        originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed — logout
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// ─── Auth API ────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post("/auth/register/", data),
  login: (data) => api.post("/auth/login/", data),
  getProfile: () => api.get("/auth/profile/"),
  updateProfile: (data) => api.put("/auth/profile/", data),
  getUsers: (params) => api.get("/auth/users/", { params }),
  deleteUser: (id) => api.delete(`/auth/users/${id}/`),
  getStats: () => api.get("/auth/stats/"),
};

// ─── Jobs API ────────────────────────────────────────────────
export const jobsAPI = {
  // Candidate
  getApprovedJobs: (params) => api.get("/jobs/approved/", { params }),
  getJobDetail: (id) => api.get(`/jobs/${id}/`),
  // Recruiter
  getMyJobs: () => api.get("/jobs/my-jobs/"),
  createJob: (data) => api.post("/jobs/create/", data),
  updateJob: (id, data) => api.put(`/jobs/${id}/edit/`, data),
  // Admin
  getAllJobs: (params) => api.get("/jobs/admin/all/", { params }),
  getPendingJobs: () => api.get("/jobs/admin/pending/"),
  approveJob: (id, data) => api.patch(`/jobs/admin/${id}/approve/`, data),
};

// ─── Candidates API ──────────────────────────────────────────
export const candidatesAPI = {
  // Candidate
  apply: (formData) => api.post("/candidates/apply/", formData),
  getMyApplications: () => api.get("/candidates/my-applications/"),
  getMyApplicationDetail: (id) => api.get(`/candidates/my-applications/${id}/`),
  // Recruiter
  getApplicants: (jobId) => api.get(`/candidates/job/${jobId}/applicants/`),
  getApplicantDetail: (id) => api.get(`/candidates/applicant/${id}/`),
  updateStatus: (id, data) => api.patch(`/candidates/applicant/${id}/status/`, data),
  // Admin
  getAllApplications: (params) => api.get("/candidates/admin/all/", { params }),
};

// ─── ML API ──────────────────────────────────────────────────
export const mlAPI = {
  getScoreStatus: (appId) => api.get(`/ml/status/${appId}/`),
  rescoreJob: (jobId) => api.post(`/ml/rescore/${jobId}/`),
  getModelInfo: () => api.get("/ml/models/"),
};

export default api;
