import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useMemo } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Card, EmptyState, ErrorState, Loading, ProgressBar, SectionTitle, StatCard } from '../../components/ui';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { HomeStackParamList } from '../../navigation/types';
import { radius, spacing } from '../../theme/colors';
import { StudentDetailData } from '../../types';
import { formatDate, formatKES } from '../../utils/format';

type Props = NativeStackScreenProps<HomeStackParamList, 'StudentDetail'>;

export default function StudentDetailScreen({ route }: Props) {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<StudentDetailData>(
    `/admin/students/${route.params.id}/`
  );

  const s = data?.student;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {loading ? (
        <Loading />
      ) : error && !data ? (
        <ErrorState message={error} onRetry={refresh} />
      ) : s ? (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.content}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        >
          <Card style={styles.headerCard}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {`${s.user.first_name?.[0] ?? ''}${s.user.last_name?.[0] ?? ''}`.toUpperCase() || 'S'}
              </Text>
            </View>
            <Text style={styles.name}>{s.user.full_name}</Text>
            <Text style={styles.meta}>{s.student_number} · {s.status}</Text>
            <Text style={styles.meta}>{s.user.email}</Text>
            <Text style={styles.meta}>{s.user.phone}</Text>
            <View style={styles.badgeRow}>
              <Badge text={s.course_name} />
              <Badge text={s.package_choice} color={colors.info} />
              <Badge text={s.branch_name} color={colors.warning} />
            </View>
            <View style={styles.progressWrap}>
              <Text style={styles.progressLabel}>
                {s.lessons_completed} / {s.total_lessons} lessons · {s.progress_percentage}%
              </Text>
              <ProgressBar value={s.progress_percentage} />
            </View>
          </Card>

          <View style={styles.statsGrid}>
            <StatCard label="Total fees" value={formatKES(s.total_fees)} icon="receipt-outline" />
            <StatCard label="Paid" value={formatKES(s.amount_paid)} icon="checkmark-circle-outline" color={colors.success} />
            <StatCard label="Balance" value={formatKES(s.balance)} icon="wallet-outline" color={colors.danger} />
          </View>

          <SectionTitle title="Assignment" />
          <Card>
            <View style={styles.infoRow}>
              <Ionicons name="person-outline" size={16} color={colors.primary} />
              <Text style={styles.infoLabel}>Instructor</Text>
              <Text style={styles.infoValue}>{s.instructor_name ?? 'Unassigned'}</Text>
            </View>
            <View style={styles.infoRow}>
              <Ionicons name="car-outline" size={16} color={colors.primary} />
              <Text style={styles.infoLabel}>Vehicle</Text>
              <Text style={styles.infoValue}>{s.vehicle_registration ?? 'Unassigned'}</Text>
            </View>
            <View style={styles.infoRow}>
              <Ionicons name="calendar-outline" size={16} color={colors.primary} />
              <Text style={styles.infoLabel}>Enrolled</Text>
              <Text style={styles.infoValue}>{formatDate(s.enrollment_date)}</Text>
            </View>
            {s.expected_graduation ? (
              <View style={styles.infoRow}>
                <Ionicons name="flag-outline" size={16} color={colors.primary} />
                <Text style={styles.infoLabel}>Expected graduation</Text>
                <Text style={styles.infoValue}>{formatDate(s.expected_graduation)}</Text>
              </View>
            ) : null}
          </Card>

          <SectionTitle title="Recent payments" />
          {data && data.payments.length > 0 ? (
            data.payments.slice(0, 10).map((p) => (
              <Card key={p.id} style={styles.itemCard}>
                <View style={styles.itemRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.itemTitle}>{formatKES(p.amount)}</Text>
                    <Text style={styles.itemMeta}>
                      {p.method_display} · {p.receipt_number} · {formatDate(p.created_at)}
                    </Text>
                  </View>
                  <Badge
                    text={p.status_display}
                    color={p.status === 'COMPLETED' ? colors.success : p.status === 'PENDING' ? colors.warning : colors.danger}
                  />
                </View>
              </Card>
            ))
          ) : (
            <EmptyState icon="card-outline" title="No payments" subtitle="Payments will appear here" />
          )}

          <SectionTitle title="Practical lessons" />
          {data && data.practical_lessons.length > 0 ? (
            data.practical_lessons.slice(0, 15).map((l) => (
              <Card key={l.id} style={styles.itemCard}>
                <View style={styles.itemRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.itemTitle}>{l.lesson_item_name}</Text>
                    <Text style={styles.itemMeta}>
                      {formatDate(l.date)} · {l.instructor_name ?? 'TBA'}
                    </Text>
                  </View>
                  <Badge text={l.status} />
                </View>
              </Card>
            ))
          ) : (
            <EmptyState icon="car-sport-outline" title="No practical lessons" />
          )}

          <SectionTitle title="Notifications sent" />
          {data && data.notifications.length > 0 ? (
            data.notifications.slice(0, 10).map((n) => (
              <Card key={n.id} style={styles.itemCard}>
                <Text style={styles.itemTitle}>{n.title}</Text>
                <Text style={styles.itemMeta}>{formatDate(n.created_at)} · {n.is_read ? 'Read' : 'Unread'}</Text>
                {n.reply ? <Text style={styles.reply}>Reply: {n.reply}</Text> : null}
              </Card>
            ))
          ) : (
            <EmptyState icon="notifications-outline" title="No notifications" />
          )}

          <View style={styles.spacer} />
        </ScrollView>
      ) : (
        <EmptyState title="Student not found" />
      )}
    </SafeAreaView>
  );
}

function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: colors.background },
    scroll: { flex: 1 },
    content: { padding: spacing.md },
    headerCard: { alignItems: 'center', paddingVertical: spacing.lg, marginBottom: spacing.sm },
    avatar: {
      width: 72,
      height: 72,
      borderRadius: 36,
      backgroundColor: colors.primary,
      alignItems: 'center',
      justifyContent: 'center',
      marginBottom: spacing.sm,
    },
    avatarText: { color: colors.onPrimary, fontSize: 26, fontWeight: '800' },
    name: { fontSize: 20, fontWeight: '800', color: colors.text },
    meta: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    badgeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, justifyContent: 'center', marginTop: spacing.sm },
    progressWrap: { alignSelf: 'stretch', marginTop: spacing.md },
    progressLabel: { fontSize: 12, color: colors.textMuted, marginBottom: 6, textAlign: 'center' },
    statsGrid: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.sm },
    infoRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: 6 },
    infoLabel: { fontSize: 13, color: colors.textMuted, width: 130 },
    infoValue: { flex: 1, fontSize: 14, fontWeight: '600', color: colors.text, textAlign: 'right' },
    itemCard: { marginBottom: spacing.sm },
    itemRow: { flexDirection: 'row', alignItems: 'center' },
    itemTitle: { fontSize: 14, fontWeight: '700', color: colors.text },
    itemMeta: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    reply: { fontSize: 12, color: colors.info, marginTop: 4 },
    spacer: { height: spacing.lg },
  });
}
