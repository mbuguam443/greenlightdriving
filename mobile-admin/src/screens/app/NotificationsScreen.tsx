import { Ionicons } from '@expo/vector-icons';
import React, { useMemo, useState } from 'react';
import { Alert, Modal, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Button, Card, EmptyState, ErrorState, FormInput, Loading, SectionTitle } from '../../components/ui';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { radius, spacing } from '../../theme/colors';
import { AdminStudent, NotificationItem, StudentsData } from '../../types';
import { formatDateTime } from '../../utils/format';

interface NotificationsData {
  notifications: NotificationItem[];
}

export default function NotificationsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<NotificationsData>('/admin/notifications/');

  const [modalOpen, setModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [ntype, setNtype] = useState('general');
  const [sendToAll, setSendToAll] = useState(true);
  const [students, setStudents] = useState<AdminStudent[]>([]);
  const [studentQuery, setStudentQuery] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<AdminStudent | null>(null);
  const [sending, setSending] = useState(false);
  const [formError, setFormError] = useState('');

  const openModal = async () => {
    setModalOpen(true);
    setTitle('');
    setMessage('');
    setNtype('general');
    setSendToAll(true);
    setSelectedStudent(null);
    setStudentQuery('');
    setFormError('');
    try {
      const { data: res } = await api.get<StudentsData>('/admin/students/?status=ACTIVE');
      setStudents(res.students);
    } catch {
      // ignore
    }
  };

  const send = async () => {
    if (!title.trim() || !message.trim()) {
      setFormError('Title and message are required.');
      return;
    }
    if (!sendToAll && !selectedStudent) {
      setFormError('Select a student or send to all.');
      return;
    }
    setFormError('');
    setSending(true);
    try {
      const payload: Record<string, unknown> = {
        title: title.trim(),
        message: message.trim(),
        notification_type: ntype,
      };
      if (sendToAll) payload.send_to_all = true;
      else payload.student = selectedStudent!.id;
      const { data: res } = await api.post<{ detail: string }>('/admin/notifications/', payload);
      setModalOpen(false);
      Alert.alert('Sent', res.detail);
      refresh();
    } catch (err) {
      setFormError(getErrorMessage(err, 'Could not send the notification.'));
    } finally {
      setSending(false);
    }
  };

  const markReplyRead = async (id: number) => {
    try {
      await api.post(`/admin/notifications/${id}/reply-read/`);
      refresh();
    } catch {
      // non-critical
    }
  };

  const filteredStudents = studentQuery.trim()
    ? students.filter(
        (s) =>
          s.user.full_name.toLowerCase().includes(studentQuery.toLowerCase()) ||
          s.student_number.toLowerCase().includes(studentQuery.toLowerCase())
      )
    : students;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.headerRow}>
        <SectionTitle title="Notification history" />
        <Pressable style={styles.sendBtn} onPress={openModal}>
          <Ionicons name="send" size={16} color={colors.onPrimary} />
          <Text style={styles.sendBtnText}>Send</Text>
        </Pressable>
      </View>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
      >
        {loading && !data ? (
          <Loading />
        ) : error && !data ? (
          <ErrorState message={error} onRetry={refresh} />
        ) : data && data.notifications.length === 0 ? (
          <EmptyState icon="notifications-off-outline" title="No notifications" subtitle="Sent notifications will appear here" />
        ) : (
          data?.notifications.map((n) => (
            <Card key={n.id} style={styles.notifCard}>
              <View style={styles.notifHeader}>
                <Text style={styles.notifTitle}>{n.title}</Text>
                <Badge text={n.notification_type_display} />
              </View>
              <Text style={styles.notifMeta}>
                {n.student_name} ({n.student_number}) · {formatDateTime(n.created_at)}
              </Text>
              <Text style={styles.notifMessage}>{n.message}</Text>
              {n.reply ? (
                <View style={styles.replyBox}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.replyLabel}>Student reply:</Text>
                    <Text style={styles.replyText}>{n.reply}</Text>
                  </View>
                  {!n.is_read ? <Badge text="New" color={colors.danger} /> : null}
                  <Pressable style={styles.replyReadBtn} onPress={() => markReplyRead(n.id)}>
                    <Ionicons name="checkmark-done" size={16} color={colors.primary} />
                  </Pressable>
                </View>
              ) : null}
            </Card>
          ))
        )}
        <View style={styles.spacer} />
      </ScrollView>

      <Modal visible={modalOpen} transparent animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Send notification</Text>

            {formError ? <Text style={styles.formError}>{formError}</Text> : null}

            <FormInput label="Title" value={title} onChangeText={setTitle} placeholder="e.g. Reminder" />
            <FormInput
              label="Message"
              value={message}
              onChangeText={setMessage}
              placeholder="Type your message..."
              multiline
              numberOfLines={4}
              style={{ minHeight: 90, textAlignVertical: 'top' }}
            />

            <Text style={styles.fieldLabel}>Type</Text>
            <View style={styles.typeRow}>
              {[
                { value: 'general', label: 'General' },
                { value: 'lesson', label: 'Lesson' },
                { value: 'payment', label: 'Payment' },
              ].map((t) => (
                <Pressable
                  key={t.value}
                  style={[styles.typeBtn, ntype === t.value && styles.typeBtnActive]}
                  onPress={() => setNtype(t.value)}
                >
                  <Text style={[styles.typeBtnText, ntype === t.value && styles.typeBtnTextActive]}>{t.label}</Text>
                </Pressable>
              ))}
            </View>

            <Text style={styles.fieldLabel}>Recipients</Text>
            <View style={styles.recipientRow}>
              <Pressable
                style={[styles.recipientBtn, sendToAll && styles.recipientBtnActive]}
                onPress={() => setSendToAll(true)}
              >
                <Text style={[styles.recipientBtnText, sendToAll && styles.recipientBtnTextActive]}>All active students</Text>
              </Pressable>
              <Pressable
                style={[styles.recipientBtn, !sendToAll && styles.recipientBtnActive]}
                onPress={() => setSendToAll(false)}
              >
                <Text style={[styles.recipientBtnText, !sendToAll && styles.recipientBtnTextActive]}>One student</Text>
              </Pressable>
            </View>

            {!sendToAll ? (
              selectedStudent ? (
                <View style={styles.selectedRow}>
                  <Text style={styles.selectedName}>{selectedStudent.user.full_name}</Text>
                  <Pressable onPress={() => setSelectedStudent(null)}>
                    <Ionicons name="close-circle" size={22} color={colors.danger} />
                  </Pressable>
                </View>
              ) : (
                <>
                  <FormInput
                    placeholder="Search student..."
                    value={studentQuery}
                    onChangeText={setStudentQuery}
                    autoCapitalize="none"
                  />
                  <View style={styles.studentList}>
                    <ScrollView style={{ maxHeight: 140 }} keyboardShouldPersistTaps="handled">
                      {filteredStudents.slice(0, 20).map((s) => (
                        <Pressable key={s.id} style={styles.studentOption} onPress={() => setSelectedStudent(s)}>
                          <Text style={styles.studentOptionName}>{s.user.full_name}</Text>
                          <Text style={styles.studentOptionMeta}>{s.student_number}</Text>
                        </Pressable>
                      ))}
                    </ScrollView>
                  </View>
                </>
              )
            ) : null}

            <View style={styles.modalActions}>
              <Button title="Cancel" variant="ghost" onPress={() => setModalOpen(false)} style={{ flex: 1 }} />
              <Button title="Send" icon="send-outline" loading={sending} onPress={send} style={{ flex: 1 }} />
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: colors.background },
    scroll: { flex: 1 },
    headerRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: spacing.md, paddingBottom: 0 },
    sendBtn: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
      backgroundColor: colors.primary,
      borderRadius: radius.md,
      paddingHorizontal: spacing.md,
      height: 40,
    },
    sendBtnText: { color: colors.onPrimary, fontWeight: '700', fontSize: 13 },
    content: { padding: spacing.md },
    notifCard: { marginBottom: spacing.sm },
    notifHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: spacing.sm },
    notifTitle: { fontSize: 14, fontWeight: '700', color: colors.text, flex: 1 },
    notifMeta: { fontSize: 12, color: colors.textMuted, marginTop: 4 },
    notifMessage: { fontSize: 13, color: colors.text, marginTop: spacing.sm },
    replyBox: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.sm,
      backgroundColor: `${colors.info}12`,
      borderRadius: radius.sm,
      padding: spacing.sm,
      marginTop: spacing.sm,
    },
    replyLabel: { fontSize: 11, fontWeight: '700', color: colors.info },
    replyText: { fontSize: 13, color: colors.text, marginTop: 2 },
    replyReadBtn: { padding: 4 },
    spacer: { height: spacing.lg },
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
      maxHeight: '90%',
    },
    modalTitle: { fontSize: 18, fontWeight: '800', color: colors.text, marginBottom: spacing.sm },
    formError: { color: colors.danger, fontSize: 13, marginBottom: spacing.sm },
    fieldLabel: { fontSize: 13, fontWeight: '600', color: colors.text, marginBottom: 6, marginTop: 6 },
    typeRow: { flexDirection: 'row', gap: 6 },
    typeBtn: {
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: radius.pill,
      borderWidth: 1,
      borderColor: colors.border,
      backgroundColor: colors.background,
    },
    typeBtnActive: { backgroundColor: colors.primary, borderColor: colors.primary },
    typeBtnText: { fontSize: 12, fontWeight: '600', color: colors.text },
    typeBtnTextActive: { color: colors.onPrimary },
    recipientRow: { flexDirection: 'row', gap: 6 },
    recipientBtn: {
      flex: 1,
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderRadius: radius.md,
      borderWidth: 1,
      borderColor: colors.border,
      backgroundColor: colors.background,
      alignItems: 'center',
    },
    recipientBtnActive: { backgroundColor: colors.primary, borderColor: colors.primary },
    recipientBtnText: { fontSize: 12, fontWeight: '600', color: colors.text },
    recipientBtnTextActive: { color: colors.onPrimary },
    selectedRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      backgroundColor: `${colors.primary}12`,
      borderRadius: radius.md,
      padding: spacing.sm,
      marginTop: spacing.sm,
    },
    selectedName: { fontSize: 14, fontWeight: '700', color: colors.text },
    studentList: {
      borderWidth: 1,
      borderColor: colors.border,
      borderRadius: radius.md,
      marginBottom: spacing.sm,
    },
    studentOption: { padding: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border },
    studentOptionName: { fontSize: 14, fontWeight: '600', color: colors.text },
    studentOptionMeta: { fontSize: 12, color: colors.textMuted, marginTop: 1 },
    modalActions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
  });
}
