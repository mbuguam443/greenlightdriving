import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import React from 'react';

import { useTheme } from '../context/ThemeContext';
import { AppTabsParamList, MoreStackParamList } from './types';
import DashboardScreen from '../screens/app/DashboardScreen';
import StudentsScreen from '../screens/app/StudentsScreen';
import StudentDetailScreen from '../screens/app/StudentDetailScreen';
import AdmissionsScreen from '../screens/app/AdmissionsScreen';
import PaymentsScreen from '../screens/app/PaymentsScreen';
import LessonsScreen from '../screens/app/LessonsScreen';
import NotificationsScreen from '../screens/app/NotificationsScreen';
import DocumentsScreen from '../screens/app/DocumentsScreen';
import EnquiriesScreen from '../screens/app/EnquiriesScreen';
import ChatScreen from '../screens/app/ChatScreen';
import ProfileScreen from '../screens/app/ProfileScreen';
import MoreScreen from '../screens/app/MoreScreen';

const Tab = createBottomTabNavigator<AppTabsParamList>();
const MoreStack = createNativeStackNavigator<MoreStackParamList>();

function MoreStackNavigator() {
  const { colors } = useTheme();
  return (
    <MoreStack.Navigator
      initialRouteName="More"
      screenOptions={{
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: colors.onPrimary,
        headerTitleStyle: { fontWeight: '700' },
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <MoreStack.Screen name="More" component={MoreScreen} options={{ title: 'Menu' }} />
      <MoreStack.Screen name="Payments" component={PaymentsScreen} />
      <MoreStack.Screen name="Lessons" component={LessonsScreen} />
      <MoreStack.Screen name="Notifications" component={NotificationsScreen} />
      <MoreStack.Screen name="Documents" component={DocumentsScreen} />
      <MoreStack.Screen name="Enquiries" component={EnquiriesScreen} />
      <MoreStack.Screen name="Chat" component={ChatScreen} />
      <MoreStack.Screen name="Profile" component={ProfileScreen} />
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
        tabBarStyle: { backgroundColor: colors.card, borderTopColor: colors.border },
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: colors.onPrimary,
        headerTitleStyle: { fontWeight: '700' },
        headerShadowVisible: false,
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={DashboardScreen}
        options={{ title: 'Dashboard', tabBarIcon: tabIcon('grid-outline') }}
      />
      <Tab.Screen
        name="StudentsTab"
        component={StudentsScreen}
        options={{ title: 'Students', tabBarIcon: tabIcon('people-outline') }}
      />
      <Tab.Screen
        name="AdmissionsTab"
        component={AdmissionsScreen}
        options={{ title: 'Admissions', tabBarIcon: tabIcon('document-text-outline') }}
      />
      <Tab.Screen
        name="MoreTab"
        component={MoreStackNavigator}
        options={{ title: 'More', headerShown: false, tabBarIcon: tabIcon('menu-outline') }}
      />
    </Tab.Navigator>
  );
}
