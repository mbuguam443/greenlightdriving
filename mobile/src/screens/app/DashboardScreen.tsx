import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Card, EmptyState, ErrorState, Loading, ProgressBar, SectionTitle } from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import { useApiData } from '../../hooks/useApiData';
import { HomeStackParamList } from '../../navigation/types';
import { colors, radius, shadows, spacing } from '../../theme/colors';
import { DashboardData } from '../../types';
import { formatDate, formatKES } from '../../utils/format';

type Props = NativeStackScreenProps<HomeStackParamList, 'Dashboard'>;

type QuickAction = {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  screen: keyof HomeStackParamList;
};

const QUICK_ACTIONS: QuickAction[] = [
  { label: 'My Lessons', icon: 'car-outline', color: colors.primary, screen: 'Lessons' },
  { label: 'Schedule', icon: 'calendar-outline', color: colors.info, screen: 'Schedule' },
  { label: 'Progress', icon: 'trending-up-outline', color: colors.warning, screen: 'Progress' },
  { label: 'Events', icon: 'megaphone-outline', color: colors.red, screen: 'Events' },
  { label: 'Documents', icon: 'documents-outline', color: '#8E24AA', screen: 'Documents' },
];

export default function DashboardScreen({ navigation }: Props) {
  const { user } = useAuth();
  const { data, loading, error, refreshing, refresh } = useApiData<DashboardData>('/student/dashboard/');

  const firstName = user?.first_name || user?.full_name?.split(' ')[0] || 'Student';

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
          <Text style={styles.greeting}>Hello, {firstName} 👋</Text>

          {data?.student ? (
            <Card style={styles.progressCard}>
              <View style={styles.progressHeader}>
                <View>
                  <Text style={styles.progressTitle}>{data.student.course_name}</Text>
                  <Text style={styles.progressSub}>
                    {data.student.branch_name} · {data.student.package_choice}
                  </Text>
                </View>
                <Badge text={data.student.status} />
              </View>
              <View style={styles.progressMeta}>
                <Text style={styles.progressPct}>{Math.round(data.progress_percentage)}% complete</Text>
                <Text style={styles.progressCount}>
                  {data.lessons_completed} / {data.total_lessons} lessons
                </Text>
              </View>
              <ProgressBar value={data.progress_percentage} />
            </Card>
          ) : (
            <Card style={styles.progressCard}>
              <Text style={styles.progressTitle}>No active enrollment</Text>
              <Text style={styles.progressSub}>
                Contact the school to apply for admission or check your enrollment status.
              </Text>
            </Card>
          )}

          <Card style={styles.balanceCard}>
            <View>
              <Text style={styles.balanceLabel}>Outstanding balance</Text>
              <Text style={styles.balanceValue}>{formatKES(data?.balance)}</Text>
            </View>
            <View style={styles.balanceMeta}>
              <Text style={styles.balanceMetaText}>Total fees: {formatKES(data?.total_fees)}</Text>
              <Text style={styles.balanceMetaText}>Paid: {formatKES(data?.amount_paid)}</Text>
            </View>
          </Card>

          <SectionTitle title="Quick actions" />
          <View style={styles.actionsGrid}>
            {QUICK_ACTIONS.map((a) => (
              <Pressable key={a.screen} style={styles.actionItem} onPress={() => navigation.navigate(a.screen)}>
                <View style={[styles.actionIcon, { backgroundColor: `${a.color}1A` }]}>
                  <Ionicons name={a.icon} size={22} color={a.color} />
                </View>
                <Text style={styles.actionLabel}>{a.label}</Text>
              </Pressable>
            ))}
          </View>

          <SectionTitle title="Upcoming lessons" />
          {data && data.upcoming_lessons.length > 0 ? (
            data.upcoming_lessons.map((l) => (
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
                  <Badge text={l.status} color={l.status === 'Scheduled' ? colors.info : colors.warning} />
                </View>
              </Card>
            ))
          ) : (
            <EmptyState icon="car-sport-outline" title="No upcoming lessons" subtitle="Your schedule will appear here" />
          )}

          <SectionTitle title="Recent payments" />
          {data && data.recent_payments.length > 0 ? (
            data.recent_payments.map((p) => (
              <Card key={p.id} style={styles.paymentCard}>
                <View style={styles.paymentRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.paymentAmount}>{formatKES(p.amount)}</Text>
                    <Text style={styles.lessonMeta}>
                      {p.receipt_number} · {formatDate(p.created_at)}
                    </Text>
                  </View>
                  <Badge
                    text={p.status_display}
                    color={p.status === 'completed' ? colors.success : p.status === 'pending' ? colors.warning : colors.danger}
                  />
                </View>
              </Card>
            ))
          ) : (
            <EmptyState icon="card-outline" title="No payments yet" subtitle="Payments you make will show here" />
          )}

          <View style={styles.spacer} />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  scroll: { flex: 1 },
  content: { padding: spacing.md, paddingTop: spacing.md },
  greeting: { fontSize: 22, fontWeight: '800', color: colors.text, marginBottom: spacing.md },
  progressCard: { marginBottom: spacing.md },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  progressTitle: { fontSize: 16, fontWeight: '700', color: colors.text },
  progressSub: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
  progressMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  progressPct: { fontSize: 13, fontWeight: '700', color: colors.primary },
  progressCount: { fontSize: 13, color: colors.textMuted },
  balanceCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.primaryDark,
  },
  balanceLabel: { color: colors.white, opacity: 0.8, fontSize: 12, fontWeight: '600' },
  balanceValue: { color: colors.white, fontSize: 24, fontWeight: '800', marginTop: 4 },
  balanceMeta: { alignItems: 'flex-end' },
  balanceMetaText: { color: colors.white, opacity: 0.85, fontSize: 12, marginTop: 2 },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  actionItem: {
    width: '30.5%',
    backgroundColor: colors.card,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    ...shadows.card,
  },
  actionIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  actionLabel: { fontSize: 12, fontWeight: '600', color: colors.text },
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
  paymentCard: { marginBottom: spacing.sm },
  paymentRow: { flexDirection: 'row', alignItems: 'center' },
  paymentAmount: { fontSize: 15, fontWeight: '700', color: colors.text },
  spacer: { height: spacing.lg },
});
