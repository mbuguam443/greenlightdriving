import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Button, Card, EmptyState, ErrorState, Loading } from '../../components/ui';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { radius, spacing } from '../../theme/colors';
import { AdmissionsData } from '../../types';
import { formatDate } from '../../utils/format';

const STATUS_FILTERS = [
  { value: '', label: 'All' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'ENROLLED', label: 'Enrolled' },
  { value: 'REJECTED', label: 'Rejected' },
];

function statusColor(status: string): 'success' | 'warning' | 'danger' | 'info' {
  switch (status) {
    case 'APPROVED':
      return 'info';
    case 'ENROLLED':
      return 'success';
    case 'REJECTED':
      return 'danger';
    default:
      return 'warning';
  }
}

export default function AdmissionsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const isFocused = useIsFocused();
  const [statusFilter, setStatusFilter] = useState('');
  const path = statusFilter ? `/admin/admissions/?status=${statusFilter}` : '/admin/admissions/';
  const { data, loading, error, refreshing, refresh } = useApiData<AdmissionsData>(path, [path]);
  const [actingId, setActingId] = useState<number | null>(null);

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  const act = async (id: number, action: 'approve' | 'reject' | 'enroll') => {
    setActingId(id);
    try {
      const { data: res } = await api.post<{ detail: string }>(`/admin/admissions/${id}/action/`, { action });
      Alert.alert('Done', res.detail);
      refresh();
    } catch (err) {
      Alert.alert('Failed', getErrorMessage(err, 'Could not update the admission.'));
    } finally {
      setActingId(null);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.filterRow}>
        {STATUS_FILTERS.map((f) => (
          <Pressable
            key={f.value || 'all'}
            style={[styles.filterBtn, statusFilter === f.value && styles.filterBtnActive]}
            onPress={() => setStatusFilter(f.value)}
          >
            <Text style={[styles.filterBtnText, statusFilter === f.value && styles.filterBtnTextActive]}>
              {f.label}
            </Text>
          </Pressable>
        ))}
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
        ) : data && data.admissions.length === 0 ? (
          <EmptyState icon="mail-outline" title="No admissions" subtitle="Applications will appear here" />
        ) : (
          data?.admissions.map((a) => (
            <Card key={a.id} style={styles.admissionCard}>
              <View style={styles.headerRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.name}>{a.full_name}</Text>
                  <Text style={styles.meta}>
                    {a.admission_number} · {formatDate(a.created_at)}
                  </Text>
                </View>
                <Badge text={a.status} color={colors[statusColor(a.status)]} />
              </View>
              <Text style={styles.meta}>
                {a.course_name} · {a.branch_name}
              </Text>
              <Text style={styles.meta}>
                {a.email} {a.phone ? `· ${a.phone}` : ''}
              </Text>

              {a.status === 'PENDING' ? (
                <View style={styles.actionRow}>
                  <Button
                    title="Approve"
                    icon="checkmark-outline"
                    loading={actingId === a.id}
                    onPress={() => act(a.id, 'approve')}
                    style={styles.actionBtn}
                  />
                  <Button
                    title="Reject"
                    variant="danger"
                    icon="close-outline"
                    loading={actingId === a.id}
                    onPress={() => act(a.id, 'reject')}
                    style={styles.actionBtn}
                  />
                </View>
              ) : a.status === 'APPROVED' ? (
                <View style={styles.actionRow}>
                  <Button
                    title="Enroll as student"
                    icon="school-outline"
                    loading={actingId === a.id}
                    onPress={() => act(a.id, 'enroll')}
                    style={{ flex: 1, height: 40 }}
                  />
                </View>
              ) : null}
            </Card>
          ))
        )}
        <View style={styles.spacer} />
      </ScrollView>
    </SafeAreaView>
  );
}

function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: colors.background },
    scroll: { flex: 1 },
    filterRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 6,
      padding: spacing.md,
      paddingBottom: 0,
    },
    filterBtn: {
      paddingHorizontal: 12,
      paddingVertical: 7,
      borderRadius: radius.pill,
      borderWidth: 1,
      borderColor: colors.border,
      backgroundColor: colors.card,
    },
    filterBtnActive: { backgroundColor: colors.primary, borderColor: colors.primary },
    filterBtnText: { fontSize: 12, fontWeight: '600', color: colors.text },
    filterBtnTextActive: { color: colors.onPrimary },
    content: { padding: spacing.md },
    admissionCard: { marginBottom: spacing.sm },
    headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: spacing.sm },
    name: { fontSize: 15, fontWeight: '700', color: colors.text },
    meta: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    actionRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
    actionBtn: { flex: 1, height: 40 },
    spacer: { height: spacing.lg },
  });
}
