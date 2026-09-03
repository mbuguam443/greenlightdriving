import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useMemo } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, Loading, ErrorState, StatCard, Badge, ProgressBar } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { StudentRecord } from '../../types';
import { AdminStackParamList } from '../../navigation/types';
import { radius, spacing } from '../../theme/colors';

type Props = NativeStackScreenProps<AdminStackParamList, 'StudentDetail'>;

export default function StudentDetailScreen({ route }: Props) {
  const { studentId } = route.params;
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data: student, loading, error, refreshing, refresh } = useApiData<StudentRecord>(`/admin/students/${studentId}/`);

  if (loading) return <Loading />;
  if (error || !student) return <ErrorState message={error || 'Student not found.'} onRetry={refresh} />;

  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
    >
      <Card>
        <Text style={[styles.name, { color: colors.text }]}>{student.full_name}</Text>
        <Text style={[styles.sub, { color: colors.textMuted }]}>{student.student_number}</Text>
        <Badge text={student.status} color={student.status === 'ACTIVE' ? colors.success : colors.warning} />
      </Card>

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
    </ScrollView>
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
  });
}
