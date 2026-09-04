import React, { useMemo } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Loading, ErrorState, StatCard } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { DashboardData } from '../../types';
import { radius, spacing } from '../../theme/colors';

function PaymentChart({ data, colors }: { data: { month: string; total: string }[]; colors: any }) {
  const styles = makeStyles(colors);
  const max = Math.max(1, ...data.map((d) => Number(d.total)));
  return (
    <View style={styles.chartWrap}>
      {data.map((d, i) => {
        const value = Number(d.total);
        const height = value > 0 ? Math.max(10, (value / max) * 100) : 4;
        const isLast = i === data.length - 1;
        return (
          <View key={d.month} style={styles.barCol}>
            <Text style={[styles.barValue, { color: colors.textMuted }]}>{value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value}</Text>
            <View style={[styles.barSlot, { backgroundColor: colors.border }]}>
                <View
                  style={[
                    styles.bar,
                    { height, backgroundColor: isLast ? colors.primary : `${colors.primary}55` },
                  ]}
                />
            </View>
            <Text style={[styles.barMonth, { color: isLast ? colors.primary : colors.textMuted }]}>{d.month}</Text>
          </View>
        );
      })}
    </View>
  );
}

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
        <StatCard label="This Month" value={`KES ${data.total_payments_this_month}`} icon="card-outline" color={colors.info} />
        <StatCard label="Total Revenue" value={`${(Number(data.total_revenue) / 1000).toFixed(1)}k`} icon="cash-outline" color={colors.success} />
      </View>
      <View style={styles.statsRow}>
        <StatCard label="Approvals" value={String(data.pending_lesson_approvals)} icon="checkmark-circle-outline" color={colors.danger} />
        <StatCard label="Owing" value={String(data.outstanding_students)} icon="alert-circle-outline" color={colors.warning} />
      </View>

      <Text style={[styles.sectionTitle, { color: colors.text }]}>Payments ({data.payments_count} total)</Text>
      <Card style={styles.chartCard}>
        {data.payment_trend && data.payment_trend.length > 0 ? (
          <PaymentChart data={data.payment_trend} colors={colors} />
        ) : (
          <Text style={[styles.chartEmpty, { color: colors.textMuted }]}>No payment data available.</Text>
        )}
      </Card>

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

function makeStyles(colors: ReturnType<typeof useTheme>['colors']) {
  return StyleSheet.create({
    container: { padding: spacing.md, paddingBottom: spacing.xl * 2 },
    greeting: { fontSize: 22, fontWeight: '800', marginBottom: spacing.md },
    statsRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.sm },
    sectionTitle: { fontSize: 16, fontWeight: '700', marginTop: spacing.lg, marginBottom: spacing.sm },
    chartCard: { marginBottom: spacing.sm },
    chartWrap: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', height: 150 },
    barCol: { flex: 1, alignItems: 'center', marginHorizontal: 4 },
    barValue: { fontSize: 10, marginBottom: 4 },
    barSlot: { width: '70%', borderRadius: radius.sm, overflow: 'hidden', justifyContent: 'flex-end', flex: 1 },
    bar: { width: '100%', borderRadius: radius.sm },
    barMonth: { fontSize: 11, fontWeight: '600', marginTop: 6 },
    chartEmpty: { textAlign: 'center', paddingVertical: spacing.xl },
    listItem: { marginBottom: spacing.sm },
    listItemRow: { flexDirection: 'row', alignItems: 'center' },
    listItemTitle: { fontSize: 14, fontWeight: '600' },
    listItemSub: { fontSize: 12, marginTop: 2 },
    listItemAmount: { fontSize: 14, fontWeight: '700' },
    listItemStatus: { fontSize: 12, fontWeight: '700' },
  });
}
