import React, { useMemo, useState } from 'react';
import {
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { Card, EmptyState, Loading, ErrorState, Badge, Button } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { AdmissionRecord } from '../../types';
import { radius, spacing } from '../../theme/colors';

export default function AdmissionsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<AdmissionRecord[]>('/admin/admissions/');
  const [search, setSearch] = useState('');

  const handleAction = async (id: number, action: 'approve' | 'reject' | 'enroll') => {
    try {
      await api.post(`/admin/admissions/${id}/${action}/`);
      Alert.alert('Success', `Admission ${action === 'approve' ? 'approved' : action === 'reject' ? 'rejected' : 'enrolled'}.`);
      refresh();
    } catch (err) {
      Alert.alert('Error', getErrorMessage(err));
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  const filtered = (data || []).filter(
    (a) =>
      a.full_name.toLowerCase().includes(search.toLowerCase()) ||
      a.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <TextInput
        placeholder="Search admissions..."
        placeholderTextColor={colors.textMuted}
        value={search}
        onChangeText={setSearch}
        style={[styles.search, { backgroundColor: colors.card, borderColor: colors.border, color: colors.text }]}
      />
      <FlatList
        data={filtered}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={filtered.length === 0 ? styles.emptyContainer : styles.list}
        ListEmptyComponent={<EmptyState icon="document-text-outline" title="No admissions found" />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <View style={styles.header}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.name, { color: colors.text }]}>{item.full_name}</Text>
                <Text style={[styles.sub, { color: colors.textMuted }]}>{item.email} - {item.phone}</Text>
              </View>
              <Badge
                text={item.status_display}
                color={item.status === 'APPROVED' ? colors.success : item.status === 'REJECTED' ? colors.danger : colors.warning}
              />
            </View>
            <View style={styles.details}>
              <Badge text={item.course_name} color={colors.primary} />
              <Badge text={item.package_choice} />
              <Badge text={item.branch_name} />
            </View>
            <Text style={[styles.date, { color: colors.textMuted }]}>Submitted: {item.submitted_at}</Text>
            {item.notes ? <Text style={[styles.notes, { color: colors.textMuted }]}>{item.notes}</Text> : null}
            {item.status === 'PENDING' && (
              <View style={styles.actions}>
                <Button title="Approve" variant="primary" onPress={() => handleAction(item.id, 'approve')} style={styles.actionBtn} />
                <Button title="Reject" variant="danger" onPress={() => handleAction(item.id, 'reject')} style={styles.actionBtn} />
              </View>
            )}
            {item.status === 'APPROVED' && (
              <View style={styles.actions}>
                <Button title="Enroll" variant="primary" onPress={() => handleAction(item.id, 'enroll')} style={styles.actionBtn} icon="school-outline" />
              </View>
            )}
          </Card>
        )}
      />
    </View>
  );
}

function makeStyles(colors: ReturnType<typeof useTheme>['colors']) {
  return StyleSheet.create({
    container: { flex: 1 },
    search: {
      margin: spacing.md,
      borderWidth: 1,
      borderRadius: radius.md,
      paddingHorizontal: spacing.md,
      paddingVertical: 10,
      fontSize: 14,
    },
    list: { paddingHorizontal: spacing.md, paddingBottom: spacing.xl },
    emptyContainer: { flex: 1 },
    card: { marginBottom: spacing.sm },
    header: { flexDirection: 'row', alignItems: 'flex-start' },
    name: { fontSize: 15, fontWeight: '700' },
    sub: { fontSize: 12, marginTop: 2 },
    details: { flexDirection: 'row', gap: 6, marginTop: spacing.sm, flexWrap: 'wrap' },
    date: { fontSize: 11, marginTop: spacing.sm },
    notes: { fontSize: 12, marginTop: spacing.sm, fontStyle: 'italic' },
    actions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
    actionBtn: { flex: 1, height: 40 },
  });
}
