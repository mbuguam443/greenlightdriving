import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useMemo, useState } from 'react';
import { Alert, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Button, Card, EmptyState, ErrorState, Loading, SectionTitle, StatCard } from '../../components/ui';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { api } from '../../services/apiClient';
import { HomeStackParamList } from '../../navigation/types';
import { radius, spacing } from '../../theme/colors';
import { DashboardData } from '../../types';
import { formatDate, formatKES } from '../../utils/format';

type Props = NativeStackScreenProps<HomeStackParamList, 'Dashboard'>;

export default function DashboardScreen({ navigation }: Props) {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<DashboardData>('/admin/dashboard/');
  const [approving, setApproving] = useState<number | null>(null);

  const approveLesson = async (id: number, action: 'approve' | 'reject') => {
    setApproving(id);
    try {
      const res = await api.post(`/admin/lessons/${id}/approve/`, { action });
      Alert.alert('Done', (res.data as { detail: string }).detail);
      refresh();
    } catch {
      Alert.alert('Failed', 'Could not update the lesson.');
    } finally {
      setApproving(null);
    }
  };

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
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        >
          <View style={styles.statsGrid}>
            <StatCard label="Active students" value={String(data?.active_students ?? 0)} icon="people-outline" />
            <StatCard label="Pending admissions" value={String(data?.pending_admissions ?? 0)} icon="mail-outline" color={colors.info} />
            <StatCard label="Approvals waiting" value={String(data?.pending_approvals_count ?? 0)} icon="checkmark-done-outline" color={colors.warning} />
            <StatCard label="Today's lessons" value={String(data?.today_lessons_count ?? 0)} icon="calendar-outline" color={colors.info} />
            <StatCard label="Revenue this month" value={formatKES(data?.month_revenue)} icon="cash-outline" />
            <StatCard label="Outstanding balance" value={formatKES(data?.outstanding_balance)} icon="wallet-outline" color={colors.danger} />
          </View>

          <SectionTitle
            title="Pending lesson approvals"
            right={
              data && data.pending_approvals_count > 0 ? (
                <Badge text={`${data.pending_approvals_count} waiting`} color={colors.warning} />
              ) : undefined
            }
          />
          {data && data.pending_approvals.length > 0 ? (
            data.pending_approvals.map((l) => (
              <Card key={l.id} style={styles.lessonCard}>
                <View style={styles.lessonRow}>
                  <View style={styles.lessonIcon}>
                    <Ionicons name="car-sport-outline" size={20} color={colors.primary} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.lessonName}>{l.lesson_item_name}</Text>
                    <Text style={styles.lessonMeta}>
                      {formatDate(l.date)} · {l.instructor_name ?? 'TBA'}
                    </Text>
                  </View>
                </View>
                <View style={styles.actionRow}>
                  <Button
                    title="Approve"
                    icon="checkmark-outline"
                    loading={approving === l.id}
                    onPress={() => approveLesson(l.id, 'approve')}
                    style={styles.actionBtn}
                  />
                  <Button
                    title="Reject"
                    variant="danger"
                    icon="close-outline"
                    loading={approving === l.id}
                    onPress={() => approveLesson(l.id, 'reject')}
                    style={styles.actionBtn}
                  />
                </View>
              </Card>
            ))
          ) : (
            <EmptyState icon="checkmark-done-outline" title="No pending approvals" subtitle="Student lesson submissions appear here" />
          )}

          <SectionTitle title="Today's lessons" />
          {data && data.today_practical.length > 0 ? (
            data.today_practical.map((l) => (
              <Card key={`p-${l.id}`} style={styles.lessonCard}>
                <View style={styles.lessonRow}>
                  <View style={styles.lessonIcon}>
                    <Ionicons name="car-sport-outline" size={20} color={colors.primary} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.lessonName}>{l.lesson_item_name}</Text>
                    <Text style={styles.lessonMeta}>
                      {l.instructor_name ?? 'TBA'} · {l.vehicle_registration ?? 'No vehicle'}
                    </Text>
                  </View>
                  <Badge text={l.status} />
                </View>
              </Card>
            ))
          ) : data && data.today_theory.length > 0 ? (
            data.today_theory.map((l) => (
              <Card key={`t-${l.id}`} style={styles.lessonCard}>
                <View style={styles.lessonRow}>
                  <View style={styles.lessonIcon}>
                    <Ionicons name="book-outline" size={20} color={colors.info} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.lessonName}>{l.topic}</Text>
                    <Text style={styles.lessonMeta}>{l.instructor_name ?? 'TBA'}</Text>
                  </View>
                  <Badge text={l.status} />
                </View>
              </Card>
            ))
          ) : (
            <EmptyState icon="calendar-outline" title="No lessons today" subtitle="Scheduled lessons for today will appear here" />
          )}

          <View style={styles.spacer} />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: colors.background },
    scroll: { flex: 1 },
    content: { padding: spacing.md },
    statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.sm },
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
    actionRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
    actionBtn: { flex: 1, height: 40 },
    spacer: { height: spacing.lg },
  });
}
