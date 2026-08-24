import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

import { api } from './apiClient';

const MESSAGE_CHANNEL_ID = 'messages';

export function setupNotificationHandler(): void {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldShowBanner: true,
      shouldShowList: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });
}

async function ensureMessageChannel(): Promise<void> {
  if (Platform.OS !== 'android') return;
  const existing = await Notifications.getNotificationChannelAsync(MESSAGE_CHANNEL_ID);
  if (existing) return;
  await Notifications.setNotificationChannelAsync(MESSAGE_CHANNEL_ID, {
    name: 'Messages',
    importance: Notifications.AndroidImportance.MAX,
    vibrationPattern: [0, 500, 500, 500],
    sound: 'default',
  });
}

async function getPermission(): Promise<boolean> {
  const current = await Notifications.getPermissionsAsync();
  if (current.status === 'granted') return true;
  const requested = await Notifications.requestPermissionsAsync();
  return requested.status === 'granted';
}

export async function registerForPushNotifications(): Promise<void> {
  try {
    await ensureMessageChannel();
    if (!(await getPermission())) return;

    const projectId = (
      Constants.expoConfig?.extra as { eas?: { projectId?: string } } | undefined
    )?.eas?.projectId;
    const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
    if (!tokenData?.data) return;
    console.log('[Push] Registering token:', tokenData.data.substring(0, 30) + '...');
    const res = await api.post('/student/push-token/', { push_token: tokenData.data });
    console.log('[Push] Server response:', res.data);
  } catch (e: any) {
    console.log('[Push] Registration failed:', e?.message || e);
  }
}
