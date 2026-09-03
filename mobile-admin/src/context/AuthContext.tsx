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
        // ignore storage errors
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await api.post<LoginPayload>('/auth/login/', { email, password });
    const STAFF_ROLES = ['SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST', 'ACCOUNTANT', 'INSTRUCTOR', 'READ_ONLY_ADMIN'];
    if (!STAFF_ROLES.includes(data.user.role)) {
      throw new Error('This account does not have staff access.');
    }
    await saveTokens(data.access, data.refresh);
    await saveUser(data.user);
    setUser(data.user);
    void registerForPushNotifications();
  };

  const logout = async () => {
    await clearAuth();
    setUser(null);
  };

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: !!user, isLoading, login, logout }),
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
