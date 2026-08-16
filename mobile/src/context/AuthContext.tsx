import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

import {
  clearAuth,
  getAccessToken,
  getStoredUser,
  saveTokens,
  saveUser,
} from '../services/apiClient';
import { api, getErrorMessage } from '../services/apiClient';
import { registerForPushNotifications } from '../services/notifications';

export interface AuthUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  role: string;
  passport_photo: string | null;
  is_verified: boolean;
}

interface LoginPayload {
  access: string;
  refresh: string;
  user: AuthUser;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
    password: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [token, storedUser] = await Promise.all([getAccessToken(), getStoredUser()]);
        if (token && storedUser) {
          setUser(storedUser as AuthUser);
          void registerForPushNotifications();
        }
      } catch {
        // ignore storage errors, fall back to logged out
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await api.post<LoginPayload>('/auth/login/', { email, password });
    await saveTokens(data.access, data.refresh);
    await saveUser(data.user);
    setUser(data.user);
    void registerForPushNotifications();
  };

  const register = async (payload: {
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
    password: string;
  }) => {
    const { data } = await api.post<LoginPayload>('/auth/register/', payload);
    await saveTokens(data.access, data.refresh);
    await saveUser(data.user);
    setUser(data.user);
    void registerForPushNotifications();
  };

  const logout = async () => {
    await clearAuth();
    setUser(null);
    await AsyncStorage.removeItem('gl_refresh_token');
  };

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: !!user, isLoading, login, register, logout }),
    [user, isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export { getErrorMessage };
