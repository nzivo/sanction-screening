import axios from "axios";

const API_BASE_URL = "/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Sanctions Lists
export const sanctionsAPI = {
  updateList: (source, force = false) =>
    api.post(
      `/lists/update/${source.toLowerCase().replace("_", "-")}?force=${force}`,
    ),

  updateAllLists: () => api.post("/lists/update/all"),

  checkUpdates: () => api.get("/lists/check-updates"),

  getSchedule: () => api.get("/lists/schedule"),

  getStatus: () => api.get("/lists/status"),

  searchSanctions: (params) => api.get("/sanctions/search", { params }),
};

// Screening
export const screeningAPI = {
  screenName: (data) => api.post("/screen", data),

  getScreeningHistory: (params) => api.get("/screening/history", { params }),

  getScreeningById: (id) => api.get(`/screening/${id}`),
};

// PEP Lists
export const pepAPI = {
  uploadPEP: (formData) =>
    api.post("/pep/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),

  searchPEP: (params) => api.get("/pep/search/", { params }),

  getPEPStats: () => api.get("/pep/stats"),

  getPEPById: (id) => api.get(`/pep/${id}`),

  updatePEP: (id, data) => api.put(`/pep/${id}`, data),

  deletePEP: (id) => api.delete(`/pep/${id}`),
};

// World Bank
export const worldBankAPI = {
  upload: (formData) =>
    api.post("/worldbank/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),

  search: (params) => api.get("/worldbank", { params }),

  getStats: () => api.get("/worldbank/stats"),

  getById: (id) => api.get(`/worldbank/${id}`),

  deactivate: (id) => api.post(`/worldbank/${id}/deactivate`),

  delete: (id) => api.delete(`/worldbank/${id}`),
};

// FRC Kenya
export const frcKenyaAPI = {
  upload: (formData) =>
    api.post("/frc-kenya/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),

  search: (params) => api.get("/frc-kenya", { params }),

  getStats: () => api.get("/frc-kenya/stats"),
};

export default api;
