import { createNativeStackNavigator } from '@react-navigation/native-stack';
import React from 'react';

import { useAuth } from '../context/AuthContext';
import { AuthStackParamList, RootStackParamList } from './types';
import AppTabs from './AppTabs';
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';

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

  return (
    <RootStack.Navigator screenOptions={{ headerShown: false }}>
      {!isLoading &&
        (isAuthenticated ? (
          <RootStack.Screen name="App" component={AppTabs} />
        ) : (
          <RootStack.Screen name="Auth" component={AuthNavigator} />
        ))}
    </RootStack.Navigator>
  );
}
