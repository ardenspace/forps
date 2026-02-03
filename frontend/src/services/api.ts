import axios from 'axios';
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  Task,
  TaskCreate,
  TaskUpdate,
} from '@/types';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - 토큰 자동 첨부
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - 401 에러 처리
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const api = {
  auth: {
    register: (data: RegisterRequest) =>
      apiClient.post<AuthResponse>('/auth/register', data),
    login: (data: LoginRequest) =>
      apiClient.post<AuthResponse>('/auth/login', data),
    me: () => apiClient.get<User>('/auth/me'),
  },
  tasks: {
    getWeek: (weekStart: string) =>
      apiClient.get<Task[]>('/tasks/week', { params: { week_start: weekStart } }),
    getById: (id: string) =>
      apiClient.get<Task>(`/tasks/${id}`),
    create: (projectId: string, data: TaskCreate) =>
      apiClient.post<Task>(`/tasks/${projectId}`, data),
    update: (id: string, data: TaskUpdate) =>
      apiClient.put<Task>(`/tasks/${id}`, data),
    delete: (id: string) =>
      apiClient.delete(`/tasks/${id}`),
  },
};

export default apiClient;
