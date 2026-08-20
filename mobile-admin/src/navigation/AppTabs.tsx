import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import React from 'react';

import { useTheme } from '../context/ThemeContext';
import { AppTabsParamList, HomeStackParamList, MoreStackParamList } from './types';
import DashboardScreen from '../screens/app/DashboardScreen';
import StudentsScreen from '../screens/app/StudentsScreen';
import StudentDetailScreen from '../screens/app/StudentDetailScreen';
import AdmissionsScreen from '../screens/app/AdmissionsScreen';
import PaymentsScreen from '../screens/app/PaymentsScreen';
import NotificationsScreen from '../screens/app/NotificationsScreen';
import ChatScreen from '../screens/app/ChatScreen';
import MoreScreen from '../screens/app/MoreScreen';
import ProfileScreen from '../screens/app/ProfileScreen';

const Tab = createBottomTabNavigator<AppTabsParamList>();
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const MoreStack = createNativeStackNavigator<MoreStackParamList>();

function HomeStackNavigator() {
  const { colors } = useTheme();
  return (
    <HomeStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: colors.onPrimary,
        headerTitleStyle: { fontWeight: '700' },
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <HomeStack.Screen name="Dashboard" component={DashboardScreen} options={{ title: 'Green Light Admin' }} />
      <HomeStack.Screen name="Admissions" component={AdmissionsScreen} options={{ title: 'Admissions' }} />
      <HomeStack.Screen name="Chat" component={ChatScreen} options={{ title: 'School Chat' }} />
      <HomeStack.Screen
        name="StudentDetail"
        component={StudentDetailScreen}
        options={({ route }) => ({ title: route.params?.name ?? 'Student' })}
      />
    </HomeStack.Navigator>
  );
}

function MoreStackNavigator() {
  const { colors } = useTheme();
  return (
    <MoreStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: colors.onPrimary,
        headerTitleStyle: { fontWeight: '700' },
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <MoreStack.Screen name="More" component={MoreScreen} options={{ title: 'More' }} />
      <MoreStack.Screen name="Profile" component={ProfileScreen} options={{ title: 'My Profile' }} />
      <MoreStack.Screen name="Notifications" component={NotificationsScreen} options={{ title: 'Notifications' }} />
      <MoreStack.Screen name="Chat" component={ChatScreen} options={{ title: 'School Chat' }} />
    </MoreStack.Navigator>
  );
}

function tabIcon(name: keyof typeof Ionicons.glyphMap) {
  return ({ color, size }: { color: string; size: number }) => (
    <Ionicons name={name} color={color} size={size} />
  );
}

export default function AppTabs() {
  const { colors } = useTheme();
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.card,
          borderTopColor: colors.border,
        },
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeStackNavigator}
        options={{ title: 'Home', tabBarIcon: tabIcon('home-outline') }}
      />
      <Tab.Screen
        name="StudentsTab"
        component={StudentsScreen}
        options={{ title: 'Students', tabBarIcon: tabIcon('people-outline') }}
      />
      <Tab.Screen
        name="PaymentsTab"
        component={PaymentsScreen}
        options={{ title: 'Payments', tabBarIcon: tabIcon('card-outline') }}
      />
      <Tab.Screen
        name="MoreTab"
        component={MoreStackNavigator}
        options={{ title: 'More', tabBarIcon: tabIcon('menu-outline') }}
      />
    </Tab.Navigator>
  );
}
