import { createNativeStackNavigator } from '@react-navigation/native-stack';
import React from 'react';

import { useAuth } from '../context/AuthContext';
import { AuthStackParamList, RootStackParamList } from './types';
import AppTabs from './AppTabs';
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';
import AdmissionGateScreen from '../screens/app/AdmissionGateScreen';
import { useAdmissionAccess } from '../hooks/useAdmissionAccess';
import { Loading } from '../components/ui';

const RootStack = createNativeStackNavigator<RootStackParamList>();
const AuthStack = createNativeStackNavigator<AuthStackParamList>();

function AuthNavigator() {
  return (
    <AuthStack.Navigator
      screenOptions={{ headerShown: false, animation: 'fade' }}
      initialRouteName="Login"
    >
      <AuthStack.Screen name="Login" component={LoginScreen} />
      <AuthStack.Screen name="Register" component={RegisterScreen} />
    </AuthStack.Navigator>
  );
}

export default function RootNavigator() {
  const { isAuthenticated, isLoading } = useAuth();
  const access = useAdmissionAccess(isAuthenticated);

  if (!isLoading && isAuthenticated && access.loading) {
    return <Loading />;
  }

  const granted = access.data?.access_level === 'granted';

  return (
    <RootStack.Navigator screenOptions={{ headerShown: false }}>
      {!isLoading &&
        (isAuthenticated ? (
          granted ? (
            <RootStack.Screen name="App" component={AppTabs} />
          ) : (
            <RootStack.Screen name="AdmissionGate">
              {() => (
                <AdmissionGateScreen
                  data={access.data}
                  loading={access.loading}
                  error={access.error}
                  refreshing={access.refreshing}
                  refresh={access.refresh}
                />
              )}
            </RootStack.Screen>
          )
        ) : (
          <RootStack.Screen name="Auth" component={AuthNavigator} />
        ))}
    </RootStack.Navigator>
  );
}