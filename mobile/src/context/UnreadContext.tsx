import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AppState } from 'react-native';

import { useAuth } from './AuthContext';
import { api } from '../services/apiClient';
import { subscribeToNotificationReceived } from '../services/notifications';
import { NotificationItem } from '../types';

interface UnreadContextValue {
  unreadCount: number;
  refreshUnread: () => Promise<void>;
}

const UnreadContext = createContext<UnreadContextValue | undefined>(undefined);

export function UnreadProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const refreshing = useRef(false);

  const refreshUnread = useCallback(async () => {
    if (!isAuthenticated || refreshing.current) return;
    refreshing.current = true;
    try {
      const { data } = await api.get<NotificationItem[]>('/student/notifications/');
      setUnreadCount(data.filter((n) => !n.is_read).length);
    } catch {
      // keep the last known count
    } finally {
      refreshing.current = false;
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refreshUnread();
  }, [refreshUnread]);

  useEffect(() => {
    const sub = AppState.addEventListener('change', (state) => {
      if (state === 'active') refreshUnread();
    });
    const notifSub = subscribeToNotificationReceived(() => refreshUnread());
    return () => {
      sub.remove();
      notifSub.remove();
    };
  }, [refreshUnread]);

  return <UnreadContext.Provider value={{ unreadCount, refreshUnread }}>{children}</UnreadContext.Provider>;
}

export function useUnread(): UnreadContextValue {
  const ctx = useContext(UnreadContext);
  if (!ctx) throw new Error('useUnread must be used within UnreadProvider');
  return ctx;
}
