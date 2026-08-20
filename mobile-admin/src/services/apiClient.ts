import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

import { API_URL } from '../config/api';

const ACCESS_KEY = 'gla_access_token';
const REFRESH_KEY = 'gla_refresh_token';
const USER_KEY = 'gla_user';

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 20000,
});

export async function getAccessToken(): Promise<string | null> {
  return AsyncStorage.getItem(ACCESS_KEY);
}

export async function saveTokens(access: string, refresh: string): Promise<void> {
  await AsyncStorage.multiSet([
    [ACCESS_KEY, access],
    [REFRESH_KEY, refresh],
  ]);
}

export async function saveUser(user: unknown): Promise<void> {
  await AsyncStorage.setItem(USER_KEY, JSON.stringify(user));
}

export async function getStoredUser(): Promise<unknown | null> {
  const raw = await AsyncStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export async function clearAuth(): Promise<void> {
  await AsyncStorage.multiRemove([ACCESS_KEY, REFRESH_KEY, USER_KEY]);
}

let isRefreshing = false;
let pendingQueue: Array<(token: string | null) => void> = [];

function onRefreshed(token: string | null) {
  pendingQueue.forEach((cb) => cb(token));
  pendingQueue = [];
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = await AsyncStorage.getItem(REFRESH_KEY);
  if (!refresh) return null;
  try {
    const { data } = await axios.post(`${API_URL}/auth/refresh/`, { refresh });
    const newAccess = data.access as string;
    await AsyncStorage.setItem(ACCESS_KEY, newAccess);
    return newAccess;
  } catch {
    await clearAuth();
    return null;
  }
}

api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const token = await getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && original && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingQueue.push((token: string | null) => {
            if (token) {
              original.headers.Authorization = `Bearer ${token}`;
              resolve(api(original));
            } else {
              resolve(Promise.reject(error));
            }
          });
        });
      }
      original._retry = true;
      isRefreshing = true;
      const newToken = await refreshAccessToken();
      onRefreshed(newToken);
      isRefreshing = false;
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      }
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(err: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { detail?: string | Record<string, unknown> } | undefined;
    if (typeof data?.detail === 'string') return data.detail;
    if (data?.detail && typeof data.detail === 'object') {
      const first = Object.values(data.detail)[0];
      if (Array.isArray(first)) return String(first[0]);
      if (first) return String(first);
    }
    if (err.response?.status === 401) return 'Your session has expired. Please log in again.';
    if (err.code === 'ECONNABORTED') return 'The request timed out. Check your connection.';
    if (!err.response) return 'Cannot reach the server. Check your connection.';
  }
  return fallback;
}
