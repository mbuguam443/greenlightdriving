import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect, useState } from 'react';
import {
  Modal,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Button, Card, EmptyState, ErrorState, FormInput, Loading, SectionTitle } from '../../components/ui';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { colors, radius, shadows, spacing } from '../../theme/colors';
import { LessonsData, LessonItemOption, PracticalLesson, TheoryLesson } from '../../types';
import { formatDate } from '../../utils/format';

type Seg = 'practical' | 'theory';

function statusColor(status: string): string {
  switch (status) {
    case 'COMPLETED':
      return colors.success;
    case 'SCHEDULED':
      return colors.info;
    case 'NOT_STARTED':
      return colors.warning;
    default:
      return colors.textMuted;
  }
}

export default function LessonsScreen() {
  const isFocused = useIsFocused();
  const { data, loading, error, refreshing, refresh } = useApiData<LessonsData>('/student/lessons/');
  const [seg, setSeg] = useState<Seg>('practical');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<LessonItemOption | null>(null);
  const [lessonDate, setLessonDate] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState('');
  const [actionError, setActionError] = useState('');
  const [attendingId, setAttendingId] = useState<number | null>(null);

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  const submitLesson = async () => {
    if (!selectedItem) {
      setActionError('Please select a lesson.');
      return;
    }
    setActionError('');
    setSubmitting(true);
    try {
      await api.post('/student/lessons/', {
        lesson_item: selectedItem.id,
        lesson_date: lessonDate || undefined,
      });
      setNotice(`"${selectedItem.name}" submitted for approval.`);
      setModalOpen(false);
      setSelectedItem(null);
      setLessonDate('');
      refresh();
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const markAttended = async (id: number, isPractical: boolean) => {
    setAttendingId(id);
    try {
      await api.post(`/student/lessons/${id}/attendance/`, {
        attendance_date: new Date().toISOString().split('T')[0],
      });
      refresh();
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setAttendingId(null);
    }
  };

  const filteredItems = data?.lesson_items.filter((i) =>
    seg === 'practical' ? i.lesson_type === 'PRACTICAL' : i.lesson_type === 'THEORY'
  ) ?? [];

  const renderPractical = (l: PracticalLesson) => (
    <Card key={`p-${l.id}`} style={styles.lessonCard}>
      <View style={styles.lessonRow}>
        <View style={styles.lessonIcon}>
          <Ionicons name="car-sport-outline" size={20} color={colors.primary} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.lessonName}>{l.lesson_item_name}</Text>
          <Text style={styles.lessonMeta}>
            {formatDate(l.date)} · {l.instructor_name ?? 'TBA'} {l.vehicle_registration ? `· ${l.vehicle_registration}` : ''}
          </Text>
          {l.remarks ? <Text style={styles.remarks}>{l.remarks}</Text> : null}
          {l.attended ? <Text style={styles.attended}>Attended</Text> : null}
        </View>
        <Badge text={l.status} color={statusColor(l.status)} />
      </View>
      {!l.attended && l.status !== 'COMPLETED' && (
        <Button
          title={attendingId === l.id ? 'Saving...' : 'Mark as attended'}
          variant="outline"
          style={styles.attendBtn}
          onPress={() => markAttended(l.id, true)}
          disabled={attendingId === l.id}
          icon="checkmark-done-outline"
        />
      )}
    </Card>
  );

  const renderTheory = (l: TheoryLesson) => (
    <Card key={`t-${l.id}`} style={styles.lessonCard}>
      <View style={styles.lessonRow}>
        <View style={[styles.lessonIcon, { backgroundColor: `${colors.info}1A` }]}>
          <Ionicons name="book-outline" size={20} color={colors.info} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.lessonName}>{l.topic || l.lesson_item_name || 'Theory lesson'}</Text>
          <Text style={styles.lessonMeta}>
            {formatDate(l.date)} · {l.instructor_name ?? 'TBA'}
          </Text>
          {l.notes ? <Text style={styles.remarks}>{l.notes}</Text> : null}
          {l.attended ? <Text style={styles.attended}>Attended</Text> : null}
        </View>
        <Badge text={l.status} color={statusColor(l.status)} />
      </View>
      {!l.attended && l.status !== 'COMPLETED' ? (
        <Button
          title={attendingId === l.id ? 'Saving...' : 'Mark as attended'}
          variant="outline"
          style={styles.attendBtn}
          onPress={() => markAttended(l.id, false)}
          disabled={attendingId === l.id}
          icon="checkmark-done-outline"
        />
      ) : null}
    </Card>
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
          {data?.summary ? (
            <Card style={styles.summaryCard}>
              <Text style={styles.summaryTitle}>
                {data.summary.completed} of {data.summary.total} lessons completed
              </Text>
              <Text style={styles.summaryMeta}>{Math.round(data.summary.progress_percentage)}% overall progress</Text>
            </Card>
          ) : null}

          {notice ? (
            <View style={styles.notice}>
              <Ionicons name="checkmark-circle-outline" size={18} color={colors.success} />
              <Text style={styles.noticeText}>{notice}</Text>
            </View>
          ) : null}
          {actionError ? <Text style={styles.errorText}>{actionError}</Text> : null}

          <View style={styles.segment}>
            {(['practical', 'theory'] as Seg[]).map((s) => (
              <Pressable
                key={s}
                style={[styles.segmentItem, seg === s && styles.segmentItemActive]}
                onPress={() => setSeg(s)}
              >
                <Text style={[styles.segmentText, seg === s && styles.segmentTextActive]}>
                  {s === 'practical' ? 'Practical' : 'Theory'}
                </Text>
              </Pressable>
            ))}
          </View>

          <SectionTitle title={seg === 'practical' ? 'Practical lessons' : 'Theory lessons'} />

          {data && (seg === 'practical' ? data.practical_lessons : data.theory_lessons).length === 0 ? (
            <EmptyState
              icon={seg === 'practical' ? 'car-sport-outline' : 'book-outline'}
              title={`No ${seg} lessons yet`}
              subtitle="Request a lesson below to get started"
            />
          ) : (
            (seg === 'practical' ? data?.practical_lessons.map(renderPractical) : data?.theory_lessons.map(renderTheory))
          )}

          <SectionTitle title="Request a lesson" />
          <Card>
            <Text style={styles.requestHint}>Pick a lesson item below and submit. An instructor will approve it.</Text>
            {filteredItems.length === 0 ? (
              <Text style={styles.errorText}>No lesson items available for this type.</Text>
            ) : (
              filteredItems.map((item) => (
                <Pressable key={item.id} style={styles.itemRow} onPress={() => setSelectedItem(item)}>
                  <View style={[styles.radio, selectedItem?.id === item.id && styles.radioActive]} />
                  <Text style={styles.itemName}>{item.name}</Text>
                </Pressable>
              ))
            )}
            <Button
              title="Submit lesson request"
              icon="send-outline"
              style={{ marginTop: spacing.sm }}
              onPress={() => setModalOpen(true)}
              disabled={!selectedItem}
            />
          </Card>
          <View style={styles.spacer} />
        </ScrollView>
      )}

      <Modal visible={modalOpen} transparent animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Confirm lesson request</Text>
            <Text style={styles.modalSub}>
              {selectedItem?.name} — leave the date blank to use today's date.
            </Text>
            <FormInput
              label="Lesson date (YYYY-MM-DD)"
              value={lessonDate}
              onChangeText={setLessonDate}
              placeholder={new Date().toISOString().split('T')[0]}
              autoCapitalize="none"
            />
            {actionError ? <Text style={styles.errorText}>{actionError}</Text> : null}
            <View style={styles.modalActions}>
              <Button title="Cancel" variant="ghost" onPress={() => setModalOpen(false)} style={{ flex: 1 }} />
              <Button title="Submit" loading={submitting} onPress={submitLesson} style={{ flex: 1 }} />
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
  summaryCard: {
    backgroundColor: colors.primaryDark,
    marginBottom: spacing.md,
  },
  summaryTitle: { color: colors.white, fontSize: 15, fontWeight: '700' },
  summaryMeta: { color: colors.white, opacity: 0.85, fontSize: 12, marginTop: 2 },
  notice: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: `${colors.success}1A`,
    padding: spacing.sm,
    borderRadius: radius.sm,
    marginBottom: spacing.sm,
  },
  noticeText: { color: colors.success, fontSize: 13, flex: 1 },
  errorText: { color: colors.danger, fontSize: 13, marginBottom: spacing.sm },
  segment: {
    flexDirection: 'row',
    backgroundColor: colors.border,
    borderRadius: radius.md,
    padding: 4,
    marginBottom: spacing.sm,
  },
  segmentItem: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: radius.sm,
  },
  segmentItemActive: { backgroundColor: colors.primary },
  segmentText: { fontSize: 13, fontWeight: '700', color: colors.textMuted },
  segmentTextActive: { color: colors.white },
  lessonCard: { marginBottom: spacing.sm },
  lessonRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  lessonIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: `${colors.primary}1A`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  lessonName: { fontSize: 14, fontWeight: '700', color: colors.text },
  lessonMeta: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
  remarks: { fontSize: 12, color: colors.text, marginTop: 4, fontStyle: 'italic' },
  attended: { fontSize: 12, color: colors.success, fontWeight: '700', marginTop: 4 },
  attendBtn: { marginTop: spacing.sm },
  requestHint: { fontSize: 13, color: colors.textMuted, marginBottom: spacing.sm },
  itemRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.sm },
  radio: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: colors.primary,
  },
  radioActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  itemName: { fontSize: 14, color: colors.text, flex: 1 },
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
  modalActions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  spacer: { height: spacing.xl },
});
