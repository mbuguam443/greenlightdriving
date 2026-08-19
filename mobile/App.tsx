import { DarkTheme, DefaultTheme, NavigationContainer, Theme } from '@react-navigation/native';
import * as Updates from 'expo-updates';
import { StatusBar } from 'expo-status-bar';
import React, { useEffect, useMemo } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AuthProvider, useAuth } from './src/context/AuthContext';
import { ThemeProvider, useTheme } from './src/context/ThemeContext';
import { UnreadProvider } from './src/context/UnreadContext';
import RootNavigator from './src/navigation/RootNavigator';
import { setupNotificationHandler } from './src/services/notifications';

setupNotificationHandler();

async function checkForUpdates() {
  try {
    if (Updates.channel === null || Updates.runtimeVersion === null) return;
    const { isAvailable } = await Updates.checkForUpdateAsync();
    if (isAvailable) {
      const { isNew } = await Updates.fetchUpdateAsync();
      if (isNew) await Updates.reloadAsync();
    }
  } catch {}
}

function LoadingScreen() {
  const { colors } = useTheme();
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background }}>
      <ActivityIndicator size="large" color={colors.primary} />
    </View>
  );
}

function AppContent() {
  const { isLoading } = useAuth();
  const { colors, isDark } = useTheme();

  const navTheme = useMemo<Theme>(() => {
    const base = isDark ? DarkTheme : DefaultTheme;
    return {
      ...base,
      colors: {
        ...base.colors,
        primary: colors.primary,
        background: colors.background,
        card: colors.card,
        text: colors.text,
        border: colors.border,
        notification: colors.danger,
      },
    };
  }, [colors, isDark]);

  if (isLoading) return <LoadingScreen />;
  return (
    <NavigationContainer theme={navTheme}>
      <StatusBar style={colors.statusBar === 'light' ? 'light' : 'dark'} />
      <RootNavigator />
    </NavigationContainer>
  );
}

export default function App() {
  useEffect(() => {
    checkForUpdates();
  }, []);
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AuthProvider>
          <UnreadProvider>
            <AppContent />
          </UnreadProvider>
        </AuthProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
