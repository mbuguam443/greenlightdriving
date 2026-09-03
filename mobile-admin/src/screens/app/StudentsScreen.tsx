import React, { useMemo, useState } from 'react';
import { FlatList, RefreshControl, StyleSheet, Text, TextInput, View } from 'react-native';

import { Card, EmptyState, Loading, ErrorState, Badge } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { StudentRecord } from '../../types';
import { radius, spacing } from '../../theme/colors';

export default function StudentsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<StudentRecord[]>('/admin/students/');
  const [search, setSearch] = useState('');

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  const filtered = (data || []).filter(
    (s) =>
      s.full_name.toLowerCase().includes(search.toLowerCase()) ||
      s.student_number.toLowerCase().includes(search.toLowerCase()) ||
      s.email.toLowerCase().includes(search.toLowerCase())
  );

  const statusColor = (status: string) => {
    if (status === 'ACTIVE') return colors.success;
    if (status === 'COMPLETED') return colors.info;
    if (status === 'EXPELLED' || status === 'WITHDRAWN') return colors.danger;
    return colors.warning;
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <TextInput
        placeholder="Search students..."
        placeholderTextColor={colors.textMuted}
        value={search}
        onChangeText={setSearch}
        style={[styles.search, { backgroundColor: colors.card, borderColor: colors.border, color: colors.text }]}
      />
      <FlatList
        data={filtered}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={filtered.length === 0 ? styles.emptyContainer : styles.list}
        ListEmptyComponent={<EmptyState icon="people-outline" title="No students found" subtitle="Try a different search" />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <Text style={[styles.name, { color: colors.text }]}>{item.full_name}</Text>
            <Text style={[styles.sub, { color: colors.textMuted }]}>{item.student_number} - {item.course_name}</Text>
            <View style={styles.row}>
              <Badge text={item.status} color={statusColor(item.status)} />
              <Text style={[styles.balance, { color: colors.danger }]}>Bal: KES {item.balance}</Text>
            </View>
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
    name: { fontSize: 15, fontWeight: '700' },
    sub: { fontSize: 12, marginTop: 2 },
    row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.sm },
    balance: { fontSize: 13, fontWeight: '600' },
  });
}
