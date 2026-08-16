import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import React from 'react';

import { colors } from '../theme/colors';
import { useUnread } from '../context/UnreadContext';
import { AppTabsParamList, HomeStackParamList, MoreStackParamList } from './types';
import DashboardScreen from '../screens/app/DashboardScreen';
import DocumentsScreen from '../screens/app/DocumentsScreen';
import EventsScreen from '../screens/app/EventsScreen';
import LessonsScreen from '../screens/app/LessonsScreen';
import MoreScreen from '../screens/app/MoreScreen';
import NotificationsScreen from '../screens/app/NotificationsScreen';
import PaymentsScreen from '../screens/app/PaymentsScreen';
import ProfileScreen from '../screens/app/ProfileScreen';
import ProgressScreen from '../screens/app/ProgressScreen';
import ScheduleScreen from '../screens/app/ScheduleScreen';

const Tab = createBottomTabNavigator<AppTabsParamList>();
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const MoreStack = createNativeStackNavigator<MoreStackParamList>();

function HomeStackNavigator() {
  return (
    <HomeStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: colors.white,
        headerTitleStyle: { fontWeight: '700' },
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <HomeStack.Screen name="Dashboard" component={DashboardScreen} options={{ title: 'Green Light' }} />
      <HomeStack.Screen name="Lessons" component={LessonsScreen} options={{ title: 'My Lessons' }} />
      <HomeStack.Screen name="Schedule" component={ScheduleScreen} options={{ title: 'Schedule' }} />
      <HomeStack.Screen name="Progress" component={ProgressScreen} options={{ title: 'Progress & NTSA' }} />
      <HomeStack.Screen name="Events" component={EventsScreen} options={{ title: 'Events' }} />
      <HomeStack.Screen name="Documents" component={DocumentsScreen} options={{ title: 'Documents' }} />
    </HomeStack.Navigator>
  );
}

function MoreStackNavigator() {
  return (
    <MoreStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: colors.white,
        headerTitleStyle: { fontWeight: '700' },
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <MoreStack.Screen name="More" component={MoreScreen} options={{ title: 'More' }} />
      <MoreStack.Screen name="Profile" component={ProfileScreen} options={{ title: 'My Profile' }} />
    </MoreStack.Navigator>
  );
}

function tabIcon(name: keyof typeof Ionicons.glyphMap) {
  return ({ color, size }: { color: string; size: number }) => (
    <Ionicons name={name} color={color} size={size} />
  );
}

export default function AppTabs() {
  const { unreadCount } = useUnread();
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: { borderTopColor: colors.border },
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeStackNavigator}
        options={{ title: 'Home', tabBarIcon: tabIcon('home-outline') }}
      />
      <Tab.Screen
        name="PaymentsTab"
        component={PaymentsScreen}
        options={{ title: 'Payments', tabBarIcon: tabIcon('card-outline') }}
      />
      <Tab.Screen
        name="NotificationsTab"
        component={NotificationsScreen}
        options={{
          title: 'Updates',
          tabBarIcon: tabIcon('notifications-outline'),
          tabBarBadge: unreadCount > 0 ? unreadCount : undefined,
          tabBarBadgeStyle: { backgroundColor: colors.danger, color: colors.white, fontWeight: '700' },
        }}
      />
      <Tab.Screen
        name="MoreTab"
        component={MoreStackNavigator}
        options={{ title: 'More', tabBarIcon: tabIcon('menu-outline') }}
      />
    </Tab.Navigator>
  );
}
