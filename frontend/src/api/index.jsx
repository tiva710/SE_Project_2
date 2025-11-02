import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { Accept: 'application/json' },
  withCredentials: true,
  timeout: 15000,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err?.response
      ? `HTTP ${err.response.status} ${err.response.statusText}: ${JSON.stringify(err.response.data)}`
      : `Network/timeout: ${err.message}`;
    return Promise.reject(new Error(msg));
  }
);

export const getStakeholdersOverview = (limit = 200) =>
  api.get('/api/graph/stakeholders/overview', { params: { limit } }).then((r) => r.data);

export const getFeaturesOverview = (limit = 200) =>
  api.get('/api/graph/features/overview', { params: { limit } }).then((r) => r.data);

export const getStakeholderNeighborhood = (id, k = 1, limit = 500) =>
  api.get('/api/graph/stakeholders/neighborhood', { params: { id, k, limit } }).then((r) => r.data);

export const getFeatureNeighborhood = (id, k = 1, limit = 500) =>
  api.get('/api/graph/features/neighborhood', { params: { id, k, limit } }).then((r) => r.data);
