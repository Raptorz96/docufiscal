export interface User {
  id: number;
  email: string;
  nome: string;
  cognome: string;
  role: string;
  is_active: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}