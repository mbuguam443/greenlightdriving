import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect, useState } from 'react';
import { Alert, Modal, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Button, EmptyState, ErrorState, FormInput, Loading } from '../../components/ui';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { useUnread } from '../../context/UnreadContext';
import { colors, radius, shadows, spacing } from '../../theme/colors';
import { NotificationItem } from '../../types';
import { formatDateTime } from '../../utils/format';

export default function NotificationsScreen() {
  const isFocused = useIsFocused();
  const { data, loading, error, refreshing, refresh } = useApiData<NotificationItem[]>('/student/notifications/');
  const { refreshUnread } = useUnread();
  const [replyingTo, setReplyingTo] = useState<NotificationItem | null>(null);
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (isFocused) {
      refresh();
      refreshUnread();
    }
  }, [isFocused]);

  const markRead = async (n: NotificationItem) => {
    if (n.is_read) return;
    try {
      await api.post(`/student/notifications/${n.id}/`, { action: 'read' });
      refresh();
      refreshUnread();
    } catch {
      // non-critical
    }
  };

  const sendReply = async () => {
    if (!replyingTo || !replyText.trim()) return;
    setSending(true);
    try {
      await api.post(`/student/notifications/${replyingTo.id}/`, { action: 'reply', reply: replyText.trim() });
      setReplyingTo(null);
      setReplyText('');
      refresh();
      refreshUnread();
    } catch (err) {
      Alert.alert('Reply failed', getErrorMessage(err));
    } finally {
      setSending(false);
    }
  };

  const sorted = [...(data ?? [])].sort(
    (a, b) => Number(a.is_read) - Number(b.is_read) || b.created_at.localeCompare(a.created_at)
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {loading ? (
        <Loading />
      ) : error && !data ? (
        <ErrorState message={error} onRetry={refresh} />
      ) : (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.content}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}
        >
          {sorted.length === 0 ? (
            <EmptyState icon="notifications-off-outline" title="No notifications" subtitle="Updates from the school will appear here" />
          ) : (
            sorted.map((n) => (
              <Pressable key={n.id} onPress={() => markRead(n)}>
                <View style={[styles.card, n.is_read && styles.cardRead]}>
                  <View style={styles.header}>
                    <View style={styles.headerLeft}>
                      <View style={[styles.dot, n.is_read && styles.dotRead]} />
                      <Text style={styles.title}>{n.title}</Text>
                    </View>
                    <Badge text={n.notification_type_display} />
                  </View>
                  <Text style={styles.message}>{n.message}</Text>
                  <Text style={styles.meta}>{formatDateTime(n.created_at)}</Text>
                  {n.reply ? (
                    <View style={styles.reply}>
                      <Text style={styles.replyLabel}>Your reply:</Text>
                      <Text style={styles.replyText}>{n.reply}</Text>
                    </View>
                  ) : null}
                  <Button
                    title="Reply"
                    variant="ghost"
                    icon="return-up-back-outline"
                    style={styles.replyBtn}
                    onPress={() => {
                      setReplyingTo(n);
                      setReplyText(n.reply ?? '');
                    }}
                  />
                </View>
              </Pressable>
            ))
          )}
          <View style={styles.spacer} />
        </ScrollView>
      )}

      <Modal visible={!!replyingTo} transparent animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Reply to notification</Text>
            <Text style={styles.modalSub}>{replyingTo?.title}</Text>
            <FormInput
              label="Your reply"
              value={replyText}
              onChangeText={setReplyText}
              multiline
              numberOfLines={4}
              style={styles.replyInput}
            />
            <View style={styles.modalActions}>
              <Button title="Cancel" variant="ghost" onPress={() => setReplyingTo(null)} style={{ flex: 1 }} />
              <Button title="Send" loading={sending} onPress={sendReply} style={{ flex: 1 }} />
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  scroll: { flex: 1 },
  content: { padding: spacing.md },
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    ...shadows.card,
    borderLeftWidth: 3,
    borderLeftColor: colors.primary,
  },
  cardRead: {
    borderLeftColor: colors.border,
    opacity: 0.85,
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, flex: 1 },
  dot: { width: 10, height: 10, borderRadius: 5, backgroundColor: colors.primary },
  dotRead: { backgroundColor: colors.border },
  title: { fontSize: 14, fontWeight: '700', color: colors.text, flex: 1 },
  message: { fontSize: 13, color: colors.text, marginTop: spacing.sm },
  meta: { fontSize: 11, color: colors.textMuted, marginTop: spacing.sm },
  reply: {
    backgroundColor: `${colors.info}12`,
    borderRadius: radius.sm,
    padding: spacing.sm,
    marginTop: spacing.sm,
  },
  replyLabel: { fontSize: 11, fontWeight: '700', color: colors.info },
  replyText: { fontSize: 13, color: colors.text, marginTop: 2 },
  replyBtn: { marginTop: spacing.sm, alignSelf: 'flex-start', height: 36 },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  modalCard: {
    width: '100%',
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    padding: spacing.lg,
    ...shadows.card,
  },
  modalTitle: { fontSize: 18, fontWeight: '800', color: colors.text },
  modalSub: { fontSize: 13, color: colors.textMuted, marginBottom: spacing.md, marginTop: 4 },
  replyInput: { minHeight: 90, textAlignVertical: 'top' },
  modalActions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  spacer: { height: spacing.lg },
});
