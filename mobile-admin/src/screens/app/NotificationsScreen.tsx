import React, { useMemo, useState } from 'react';
import {
  Alert,
  FlatList,
  Pressable,
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
import { NotificationRecord, StudentRecord } from '../../types';
import { radius, spacing } from '../../theme/colors';

const NOTIFICATION_TYPES = [
  { value: 'general', label: 'General' },
  { value: 'lesson', label: 'Lesson' },
  { value: 'payment', label: 'Payment' },
];

function Chip({
  label,
  active,
  onPress,
  colors,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
  colors: any;
}) {
  const styles = makeStyles(colors);
  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.chip,
        { borderColor: active ? colors.primary : colors.border, backgroundColor: active ? `${colors.primary}1A` : colors.card },
      ]}
    >
      <Text style={[styles.chipText, { color: active ? colors.primary : colors.text }]}>{label}</Text>
    </Pressable>
  );
}

export default function NotificationsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<NotificationRecord[]>('/admin/notifications/');
  const { data: students } = useApiData<StudentRecord[]>('/admin/students/', []);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [ntype, setNtype] = useState('general');
  const [sendAll, setSendAll] = useState(true);
  const [studentId, setStudentId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSend = async () => {
    if (!title.trim() || !message.trim()) {
      Alert.alert('Error', 'Please enter a title and message.');
      return;
    }
    if (!sendAll && !studentId) {
      Alert.alert('Error', 'Please select a student, or choose "All students".');
      return;
    }
    const payload: Record<string, unknown> = {
      title: title.trim(),
      message: message.trim(),
      notification_type: ntype,
    };
    if (sendAll) {
      payload.target_audience = 'ALL';
    } else {
      payload.student = studentId;
    }
    setSubmitting(true);
    try {
      await api.post('/admin/notifications/', payload);
      Alert.alert('Sent', sendAll ? 'Notification sent to all students.' : 'Notification sent to the selected student.');
      setTitle('');
      setMessage('');
      setNtype('general');
      setSendAll(true);
      setStudentId(null);
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
        <View style={styles.formWrap}>
          <Card style={styles.formCard}>
            <Text style={[styles.fieldLabel, { color: colors.text }]}>Notification type</Text>
            <View style={styles.chipWrap}>
              {NOTIFICATION_TYPES.map((t) => (
                <Chip key={t.value} label={t.label} active={ntype === t.value} onPress={() => setNtype(t.value)} colors={colors} />
              ))}
            </View>

            <Text style={[styles.fieldLabel, { color: colors.text }]}>Recipients</Text>
            <View style={styles.chipWrap}>
              <Chip label="All students" active={sendAll} onPress={() => { setSendAll(true); setStudentId(null); }} colors={colors} />
              <Chip label="Specific student" active={!sendAll} onPress={() => setSendAll(false)} colors={colors} />
            </View>

            <FormInput label="Title" value={title} onChangeText={setTitle} placeholder="Notification title" />
            <FormInput label="Message" value={message} onChangeText={setMessage} placeholder="Notification message" multiline numberOfLines={3} style={{ height: 80, textAlignVertical: 'top' }} />

            {!sendAll && (
              <>
                <Text style={[styles.fieldLabel, { color: colors.text }]}>Student</Text>
                <View style={styles.chipWrap}>
                  {(students || []).map((s) => (
                    <Chip
                      key={s.id}
                      label={`${s.full_name} · ${s.student_number}`}
                      active={studentId === s.id}
                      onPress={() => setStudentId(s.id)}
                      colors={colors}
                    />
                  ))}
                  {!students || students.length === 0 ? (
                    <Text style={[styles.hint, { color: colors.textMuted }]}>No students available.</Text>
                  ) : null}
                </View>
              </>
            )}

            <Button title="Send" onPress={handleSend} loading={submitting} icon="send-outline" />
          </Card>
        </View>
      )}

      <FlatList
        data={data || []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={!data || data.length === 0 ? styles.emptyContainer : styles.list}
        ListEmptyComponent={showForm ? null : <EmptyState icon="notifications-off-outline" title="No notifications yet" />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <View style={styles.header}>
              <Text style={[styles.title, { color: colors.text }]}>{item.title}</Text>
              <Badge
                text={item.notification_type_display}
                color={item.notification_type === 'payment' ? colors.danger : item.notification_type === 'lesson' ? colors.info : colors.primary}
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
    formWrap: { marginHorizontal: spacing.md },
    formCard: { marginBottom: spacing.md },
    fieldLabel: { fontSize: 13, fontWeight: '600', marginTop: spacing.sm, marginBottom: 6 },
    chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.sm },
    chip: { paddingHorizontal: spacing.md, paddingVertical: 8, borderRadius: radius.pill, borderWidth: 1.5 },
    chipText: { fontSize: 12, fontWeight: '600' },
    hint: { fontSize: 12, fontStyle: 'italic' },
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
