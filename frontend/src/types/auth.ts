export interface User {
  id: number;
  email: string;
  nome: string;
  cognome: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterData {
  email: string;
  password: string;
  nome: string;
  cognome: string;
}

export interface ProfileUpdate {
  nome?: string;
  cognome?: string;
  email?: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}