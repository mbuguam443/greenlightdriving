import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useColorScheme } from 'react-native';

export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeColors {
  primary: string;
  primaryDark: string;
  primaryLight: string;
  white: string;
  onPrimary: string;
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
  chatMe: string;
  chatOther: string;
  statusBar: 'light' | 'dark';
}

export const lightColors: ThemeColors = {
  primary: '#2E7D32',
  primaryDark: '#1B5E20',
  primaryLight: '#66BB6A',
  white: '#FFFFFF',
  onPrimary: '#FFFFFF',
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
  chatMe: '#DCF8C6',
  chatOther: '#FFFFFF',
  statusBar: 'dark',
};

export const darkColors: ThemeColors = {
  primary: '#2E7D32',
  primaryDark: '#1B5E20',
  primaryLight: '#66BB6A',
  white: '#FFFFFF',
  onPrimary: '#FFFFFF',
  darkGray: '#E0E0E0',
  red: '#EF5350',
  yellow: '#FFD54F',
  background: '#121212',
  card: '#1E1E1E',
  text: '#E8E8E8',
  textMuted: '#A0A0A0',
  border: '#333333',
  success: '#66BB6A',
  warning: '#FFD54F',
  danger: '#EF5350',
  info: '#4FC3F7',
  inputBg: '#2A2A2A',
  inputText: '#E8E8E8',
  chatMe: '#1B4332',
  chatOther: '#2A2A2A',
  statusBar: 'light',
};

const THEME_KEY = 'gl_admin_theme_mode';

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
  const colors = useMemo(() => (isDark ? darkColors : lightColors), [isDark]);

  const value = useMemo(() => ({ mode, setMode, colors, isDark }), [mode, setMode, colors, isDark]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}
