import api from './api';
import type { LoginCredentials, AuthResponse, User, ProfileUpdate, PasswordChangeRequest } from '../types/auth';

export const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.email);
  formData.append('password', credentials.password);

  const response = await api.post<AuthResponse>('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  return response.data;
};

export const getMe = async (): Promise<User> => {
  const response = await api.get<User>('/auth/me');
  return response.data;
};

export const saveToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

export const removeToken = (): void => {
  localStorage.removeItem('access_token');
};

export const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

export const updateProfile = async (data: ProfileUpdate): Promise<User> => {
  const response = await api.patch<User>('/auth/me', data);
  return response.data;
};

export const changePassword = async (data: PasswordChangeRequest): Promise<void> => {
  await api.post('/auth/change-password', data);
};