import { NavigationContainer } from '@react-navigation/native';
import * as Updates from 'expo-updates';
import { StatusBar } from 'expo-status-bar';
import React, { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AuthProvider, useAuth } from './src/context/AuthContext';
import { UnreadProvider } from './src/context/UnreadContext';
import RootNavigator from './src/navigation/RootNavigator';
import { setupNotificationHandler } from './src/services/notifications';
import { colors } from './src/theme/colors';

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
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background }}>
      <ActivityIndicator size="large" color={colors.primary} />
    </View>
  );
}

function AppContent() {
  const { isLoading } = useAuth();
  if (isLoading) return <LoadingScreen />;
  return (
    <NavigationContainer>
      <RootNavigator />
    </NavigationContainer>
  );
}

export default function App() {
  useEffect(() => { checkForUpdates(); }, []);
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <UnreadProvider>
          <StatusBar style="auto" />
          <AppContent />
        </UnreadProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
