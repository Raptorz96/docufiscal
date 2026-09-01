import React, { useEffect, useState } from 'react';
import type { User, LoginCredentials } from '../types/auth';
import * as authService from '../services/authService';
import { AuthContext, type AuthContextType } from './authContext';

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = authService.getToken();
      if (token) {
        try {
          const userData = await authService.getMe();
          setUser(userData);
        } catch (error) {
          console.error('Failed to validate token:', error);
          authService.removeToken();
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    const response = await authService.login(credentials);
    authService.saveToken(response.access_token);
    const userData = await authService.getMe();
    setUser(userData);
  };

  const logout = (): void => {
    authService.removeToken();
    setUser(null);
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const userData = await authService.getMe();
      setUser(userData);
    } catch {
      authService.removeToken();
      setUser(null);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};