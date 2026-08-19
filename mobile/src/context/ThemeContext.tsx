import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useColorScheme } from 'react-native';

export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeColors {
  primary: string;
  primaryDark: string;
  primaryLight: string;
  white: string;
  darkGray: string;
  red: string;
  yellow: string;
  background: string;
  card: string;
  text: string;
  textMuted: string;
  border: string;
  success: string;
  warning: string;
  danger: string;
  info: string;
  inputBg: string;
  inputText: string;
  statusBar: 'light' | 'dark';
}

const lightColors: ThemeColors = {
  primary: '#2E7D32',
  primaryDark: '#1B5E20',
  primaryLight: '#66BB6A',
  white: '#FFFFFF',
  darkGray: '#263238',
  red: '#D32F2F',
  yellow: '#FBC02D',
  background: '#F4F7F5',
  card: '#FFFFFF',
  text: '#263238',
  textMuted: '#6B7A6F',
  border: '#E0E8E1',
  success: '#2E7D32',
  warning: '#FBC02D',
  danger: '#D32F2F',
  info: '#0288D1',
  inputBg: '#FFFFFF',
  inputText: '#263238',
  statusBar: 'dark',
};

const darkColors: ThemeColors = {
  primary: '#66BB6A',
  primaryDark: '#2E7D32',
  primaryLight: '#81C784',
  white: '#121212',
  darkGray: '#E0E0E0',
  red: '#EF5350',
  yellow: '#FFD54F',
  background: '#121212',
  card: '#1E1E1E',
  text: '#E0E0E0',
  textMuted: '#9E9E9E',
  border: '#333333',
  success: '#66BB6A',
  warning: '#FFD54F',
  danger: '#EF5350',
  info: '#4FC3F7',
  inputBg: '#2A2A2A',
  inputText: '#E0E0E0',
  statusBar: 'light',
};

const THEME_KEY = 'gl_theme_mode';

interface ThemeContextValue {
  mode: ThemeMode;
  setMode: (m: ThemeMode) => void;
  colors: ThemeColors;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextValue>({
  mode: 'system',
  setMode: () => {},
  colors: lightColors,
  isDark: false,
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const systemScheme = useColorScheme();
  const [mode, setModeState] = useState<ThemeMode>('system');

  useEffect(() => {
    AsyncStorage.getItem(THEME_KEY).then((v) => {
      if (v === 'light' || v === 'dark' || v === 'system') setModeState(v);
    });
  }, []);

  const setMode = useCallback((m: ThemeMode) => {
    setModeState(m);
    AsyncStorage.setItem(THEME_KEY, m);
  }, []);

  const isDark = mode === 'system' ? systemScheme === 'dark' : mode === 'dark';
  const colors = isDark ? darkColors : lightColors;

  return (
    <ThemeContext.Provider value={{ mode, setMode, colors, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
