import Constants, { ExecutionEnvironment } from 'expo-constants';
import { isRunningInExpoGo } from 'expo';
import { Platform } from 'react-native';

import { api } from './apiClient';

const MESSAGE_CHANNEL_ID = 'messages';

export const notificationsUnavailable =
  Platform.OS === 'android' &&
  (isRunningInExpoGo() ||
    Constants.executionEnvironment === ExecutionEnvironment.StoreClient);

const Notifications: typeof import('expo-notifications') | null = notificationsUnavailable
  ? null
  : (require('expo-notifications') as typeof import('expo-notifications'));

export function subscribeToNotificationReceived(listener: () => void): { remove: () => void } {
  if (!Notifications) return { remove: () => {} };
  return Notifications.addNotificationReceivedListener(listener);
}

export function setupNotificationHandler(): void {
  if (!Notifications) return;
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
  if (!Notifications || Platform.OS !== 'android') return;
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
  if (!Notifications) return false;
  const current = await Notifications.getPermissionsAsync();
  if (current.status === 'granted') return true;
  const requested = await Notifications.requestPermissionsAsync();
  return requested.status === 'granted';
}

export async function registerForPushNotifications(): Promise<void> {
  if (!Notifications || notificationsUnavailable) {
    console.log('[Push] Skipped: remote push notifications are unavailable in this environment.');
    return;
  }
  try {
    await ensureMessageChannel();
    if (!(await getPermission())) return;

    const projectId = (
      Constants.expoConfig?.extra as { eas?: { projectId?: string } } | undefined
    )?.eas?.projectId;
    const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
    if (!tokenData?.data) return;
    console.log('[Push] Registering token:', tokenData.data.substring(0, 30) + '...');
    const res = await api.post('/admin/push-token/', { push_token: tokenData.data });
    console.log('[Push] Server response:', res.data);
  } catch (e: any) {
    console.log('[Push] Registration failed:', e?.message || e);
  }
}
