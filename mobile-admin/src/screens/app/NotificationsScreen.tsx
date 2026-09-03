import React, { useMemo, useState } from 'react';
import {
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { Card, EmptyState, Loading, ErrorState, Badge, Button, FormInput } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { NotificationRecord } from '../../types';
import { radius, spacing } from '../../theme/colors';

export default function NotificationsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<NotificationRecord[]>('/admin/notifications/');
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSend = async () => {
    if (!title.trim() || !message.trim()) {
      Alert.alert('Error', 'Please enter a title and message.');
      return;
    }
    setSubmitting(true);
    try {
      await api.post('/admin/notifications/', { title: title.trim(), message: message.trim(), notification_type: 'INFO', target_audience: 'ALL' });
      Alert.alert('Sent', 'Notification sent to all students.');
      setTitle('');
      setMessage('');
      setShowForm(false);
      refresh();
    } catch (err) {
      Alert.alert('Error', getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Button
        title={showForm ? 'Cancel' : 'Send Notification'}
        variant={showForm ? 'outline' : 'primary'}
        onPress={() => setShowForm(!showForm)}
        icon={showForm ? 'close-outline' : 'send-outline'}
        style={styles.sendBtn}
      />

      {showForm && (
        <Card style={styles.formCard}>
          <FormInput label="Title" value={title} onChangeText={setTitle} placeholder="Notification title" />
          <FormInput label="Message" value={message} onChangeText={setMessage} placeholder="Notification message" multiline numberOfLines={3} style={{ height: 80, textAlignVertical: 'top' }} />
          <Button title="Send" onPress={handleSend} loading={submitting} icon="send-outline" />
        </Card>
      )}

      <FlatList
        data={data || []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={!data || data.length === 0 ? styles.emptyContainer : styles.list}
        ListEmptyComponent={<EmptyState icon="notifications-off-outline" title="No notifications yet" />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <View style={styles.header}>
              <Text style={[styles.title, { color: colors.text }]}>{item.title}</Text>
              <Badge
                text={item.notification_type_display}
                color={item.notification_type === 'URGENT' ? colors.danger : colors.info}
              />
            </View>
            <Text style={[styles.message, { color: colors.textMuted }]}>{item.message}</Text>
            <View style={styles.footer}>
              <Text style={[styles.target, { color: colors.textMuted }]}>{item.target_audience_display} - {item.recipient_count} recipients</Text>
              <Text style={[styles.date, { color: colors.textMuted }]}>{item.created_at}</Text>
            </View>
          </Card>
        )}
      />
    </View>
  );
}

function makeStyles(colors: ReturnType<typeof useTheme>['colors']) {
  return StyleSheet.create({
    container: { flex: 1 },
    sendBtn: { margin: spacing.md },
    formCard: { marginBottom: spacing.md, marginHorizontal: spacing.md },
    list: { paddingHorizontal: spacing.md, paddingBottom: spacing.xl },
    emptyContainer: { flex: 1 },
    card: { marginBottom: spacing.sm },
    header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
    title: { fontSize: 15, fontWeight: '700', flex: 1 },
    message: { fontSize: 13, marginTop: spacing.sm },
    footer: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.sm },
    target: { fontSize: 11 },
    date: { fontSize: 11 },
  });
}
