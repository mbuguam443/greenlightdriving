import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useMemo, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Loading, ErrorState, Badge, ProgressBar, EmptyState } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { StudentDetail } from '../../types';
import { AdminStackParamList } from '../../navigation/types';
import { radius, spacing } from '../../theme/colors';

type Props = NativeStackScreenProps<AdminStackParamList, 'StudentDetail'>;

type Tab = 'overview' | 'payments' | 'lessons' | 'notifications';

const TABS: { key: Tab; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'payments', label: 'Payments' },
  { key: 'lessons', label: 'Lessons' },
  { key: 'notifications', label: 'Notifications' },
];

export default function StudentDetailScreen({ route }: Props) {
  const { studentId } = route.params;
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<StudentDetail>(`/admin/students/${studentId}/`);
  const [tab, setTab] = useState<Tab>('overview');

  if (loading) return <Loading />;
  if (error || !data) return <ErrorState message={error || 'Student not found.'} onRetry={refresh} />;

  const { student } = data;

  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
    >
      <Card>
        <Text style={[styles.name, { color: colors.text }]}>{student.full_name}</Text>
        <Text style={[styles.sub, { color: colors.textMuted }]}>{student.student_number} · {student.email}</Text>
        <Badge text={student.status} color={student.status === 'ACTIVE' ? colors.success : colors.warning} />
      </Card>

      <View style={styles.tabs}>
        {TABS.map((t) => {
          const active = tab === t.key;
          return (
            <Pressable
              key={t.key}
              onPress={() => setTab(t.key)}
              style={[
                styles.tab,
                { borderColor: active ? colors.primary : colors.border, backgroundColor: active ? `${colors.primary}1A` : colors.card },
              ]}
            >
              <Text style={[styles.tabText, { color: active ? colors.primary : colors.text }]}>{t.label}</Text>
            </Pressable>
          );
        })}
      </View>

      {tab === 'overview' ? <OverviewTab student={student as any} colors={colors} styles={styles} /> : null}
      {tab === 'payments' ? <PaymentsTab payments={data.payments} studentName={student.full_name} colors={colors} styles={styles} /> : null}
      {tab === 'lessons' ? <LessonsTab lessons={data.lessons} studentName={student.full_name} colors={colors} styles={styles} /> : null}
      {tab === 'notifications' ? <NotificationsTab notifications={data.notifications} colors={colors} styles={styles} /> : null}
    </ScrollView>
  );
}

function OverviewTab({ student, colors, styles }: { student: any; colors: any; styles: any }) {
  return (
    <>
      <Card style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Course Details</Text>
        <InfoRow label="Course" value={student.course_name} colors={colors} />
        <InfoRow label="Category" value={student.category_name} colors={colors} />
        <InfoRow label="Package" value={student.package_choice} colors={colors} />
        <InfoRow label="Branch" value={student.branch_name} colors={colors} />
        <InfoRow label="Instructor" value={student.instructor_name || 'Not assigned'} colors={colors} />
        <InfoRow label="Enrolled" value={student.enrollment_date} colors={colors} />
      </Card>

      <Card style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Progress</Text>
        <ProgressBar value={student.progress_percentage} />
        <Text style={[styles.progressText, { color: colors.textMuted }]}>{student.lessons_completed}/{student.total_lessons} lessons ({student.progress_percentage}%)</Text>
      </Card>

      <Card style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Financial</Text>
        <InfoRow label="Total Fees" value={`KES ${student.total_fees}`} colors={colors} />
        <InfoRow label="Paid" value={`KES ${student.amount_paid}`} colors={colors} valueColor={colors.success} />
        <InfoRow label="Balance" value={`KES ${student.balance}`} colors={colors} valueColor={colors.danger} />
      </Card>
    </>
  );
}

function PaymentsTab({ payments, studentName, colors, styles }: { payments: any[]; studentName: string; colors: any; styles: any }) {
  if (!payments.length) {
    return <EmptyState icon="card-outline" title="No payments yet" subtitle={`No payments recorded for ${studentName}.`} />;
  }
  return (
    <>
      {payments.map((p) => (
        <Card key={p.id} style={styles.section}>
          <View style={styles.rowBetween}>
            <Text style={[styles.itemMain, { color: colors.text }]}>{p.receipt_number}</Text>
            <Text style={[styles.itemAmount, { color: colors.success }]}>KES {p.amount}</Text>
          </View>
          <View style={styles.chips}>
            <Badge text={p.method_display} />
            <Badge text={p.status_display} color={p.status === 'COMPLETED' ? colors.success : colors.warning} />
            <Text style={[styles.itemSub, { color: colors.textMuted }]}>{p.created_at}</Text>
          </View>
          {p.description ? <Text style={[styles.itemSub, { color: colors.textMuted }]}>{p.description}</Text> : null}
        </Card>
      ))}
    </>
  );
}

function LessonsTab({ lessons, studentName, colors, styles }: { lessons: any[]; studentName: string; colors: any; styles: any }) {
  if (!lessons.length) {
    return <EmptyState icon="book-outline" title="No lessons yet" subtitle={`No lessons scheduled for ${studentName}.`} />;
  }
  return (
    <>
      {lessons.map((l) => (
        <Card key={l.id} style={styles.section}>
          <Text style={[styles.itemMain, { color: colors.text }]}>{l.lesson_item_name}</Text>
          <View style={styles.chips}>
            <Badge text={l.lesson_type} />
            <Badge text={l.status} color={l.status === 'COMPLETED' ? colors.success : colors.warning} />
            <Text style={[styles.itemSub, { color: colors.textMuted }]}>{l.date}</Text>
          </View>
          {l.instructor_name ? (
            <Text style={[styles.itemSub, { color: colors.textMuted }]}>Instructor: {l.instructor_name}</Text>
          ) : null}
          {l.remarks ? <Text style={[styles.itemSub, { color: colors.textMuted }]}>{l.remarks}</Text> : null}
        </Card>
      ))}
    </>
  );
}

function NotificationsTab({ notifications, colors, styles }: { notifications: any[]; colors: any; styles: any }) {
  if (!notifications.length) {
    return <EmptyState icon="notifications-outline" title="No notifications" />;
  }
  return (
    <>
      {notifications.map((n) => (
        <Card key={n.id} style={styles.section}>
          <View style={styles.rowBetween}>
            <Text style={[styles.itemMain, { color: colors.text }]}>{n.title}</Text>
            {n.is_read ? null : <Badge text="New" color={colors.primary} />}
          </View>
          <Text style={[styles.itemSub, { color: colors.textMuted }]}>{n.message}</Text>
          <Text style={[styles.itemSmall, { color: colors.textMuted }]}>{n.created_at}</Text>
        </Card>
      ))}
    </>
  );
}

function InfoRow({ label, value, colors, valueColor }: { label: string; value: string; colors: any; valueColor?: string }) {
  return (
    <View style={infoStyles.row}>
      <Text style={[infoStyles.label, { color: colors.textMuted }]}>{label}</Text>
      <Text style={[infoStyles.value, { color: valueColor || colors.text }]}>{value}</Text>
    </View>
  );
}

const infoStyles = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  label: { fontSize: 13 },
  value: { fontSize: 13, fontWeight: '600' },
});

function makeStyles(colors: ReturnType<typeof useTheme>['colors']) {
  return StyleSheet.create({
    container: { padding: spacing.md, paddingBottom: spacing.xl * 2 },
    name: { fontSize: 20, fontWeight: '800' },
    sub: { fontSize: 13, marginTop: 2, marginBottom: spacing.sm },
    section: { marginTop: spacing.md },
    sectionTitle: { fontSize: 15, fontWeight: '700', marginBottom: spacing.sm },
    progressText: { fontSize: 12, marginTop: 4, textAlign: 'center' },
    tabs: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md },
    tab: {
      paddingHorizontal: spacing.md,
      paddingVertical: 8,
      borderRadius: radius.pill,
      borderWidth: 1.5,
    },
    tabText: { fontSize: 12, fontWeight: '600' },
    rowBetween: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
    chips: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.sm, flexWrap: 'wrap' },
    itemMain: { fontSize: 14, fontWeight: '700' },
    itemSub: { fontSize: 12, marginTop: 4 },
    itemSmall: { fontSize: 11, marginTop: 4 },
    itemAmount: { fontSize: 14, fontWeight: '800' },
  });
}
