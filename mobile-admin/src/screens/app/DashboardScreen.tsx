import React, { useMemo } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Loading, ErrorState, StatCard } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { DashboardData } from '../../types';
import { radius, spacing } from '../../theme/colors';

export default function DashboardScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<DashboardData>('/admin/dashboard/');

  if (loading) return <Loading />;
  if (error || !data) return <ErrorState message={error || 'Failed to load dashboard.'} onRetry={refresh} />;

  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
    >
      <Text style={[styles.greeting, { color: colors.text }]}>Dashboard Overview</Text>

      <View style={styles.statsRow}>
        <StatCard label="Students" value={String(data.total_students)} icon="people-outline" color={colors.primary} />
        <StatCard label="Active" value={String(data.active_students)} icon="person-outline" color={colors.success} />
      </View>
      <View style={styles.statsRow}>
        <StatCard label="Payments" value={`KES ${data.total_payments_this_month}`} icon="card-outline" color={colors.info} />
        <StatCard label="Pending" value={String(data.pending_admissions)} icon="document-text-outline" color={colors.warning} />
      </View>
      <View style={styles.statsRow}>
        <StatCard label="Approvals" value={String(data.pending_lesson_approvals)} icon="checkmark-circle-outline" color={colors.danger} />
        <StatCard label="Messages" value={String(data.unread_messages)} icon="chatbubbles-outline" color={colors.primaryDark} />
      </View>

      {data.recent_payments?.length > 0 && (
        <>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Recent Payments</Text>
          {data.recent_payments.map((p) => (
            <Card key={p.id} style={styles.listItem}>
              <View style={styles.listItemRow}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.listItemTitle, { color: colors.text }]}>{p.student_name}</Text>
                  <Text style={[styles.listItemSub, { color: colors.textMuted }]}>{p.receipt_number} - {p.method_display}</Text>
                </View>
                <Text style={[styles.listItemAmount, { color: colors.success }]}>KES {p.amount}</Text>
              </View>
            </Card>
          ))}
        </>
      )}

      {data.recent_admissions?.length > 0 && (
        <>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Recent Admissions</Text>
          {data.recent_admissions.map((a) => (
            <Card key={a.id} style={styles.listItem}>
              <View style={styles.listItemRow}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.listItemTitle, { color: colors.text }]}>{a.full_name}</Text>
                  <Text style={[styles.listItemSub, { color: colors.textMuted }]}>{a.course_name} - {a.package_choice}</Text>
                </View>
                <Text style={[styles.listItemStatus, { color: a.status === 'APPROVED' ? colors.success : colors.warning }]}>{a.status_display}</Text>
              </View>
            </Card>
          ))}
        </>
      )}
    </ScrollView>
  );
}

function makeStyles(colors: typeof useTheme extends () => infer R ? R extends { colors: infer C } ? C : never : never) {
  return StyleSheet.create({
    container: { padding: spacing.md, paddingBottom: spacing.xl * 2 },
    greeting: { fontSize: 22, fontWeight: '800', marginBottom: spacing.md },
    statsRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.sm },
    sectionTitle: { fontSize: 16, fontWeight: '700', marginTop: spacing.lg, marginBottom: spacing.sm },
    listItem: { marginBottom: spacing.sm },
    listItemRow: { flexDirection: 'row', alignItems: 'center' },
    listItemTitle: { fontSize: 14, fontWeight: '600' },
    listItemSub: { fontSize: 12, marginTop: 2 },
    listItemAmount: { fontSize: 14, fontWeight: '700' },
    listItemStatus: { fontSize: 12, fontWeight: '700' },
  });
}
