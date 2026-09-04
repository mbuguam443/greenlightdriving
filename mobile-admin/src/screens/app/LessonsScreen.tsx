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
import { LessonRecord } from '../../types';
import { radius, spacing } from '../../theme/colors';

export default function LessonsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<LessonRecord[]>('/admin/lessons/');
  const [search, setSearch] = useState('');

  const handleApprove = async (id: number) => {
    try {
      await api.post(`/admin/lessons/${id}/approve/`);
      Alert.alert('Approved', 'Lesson has been approved.');
      refresh();
    } catch (err) {
      Alert.alert('Error', getErrorMessage(err));
    }
  };

  const handleReject = async (id: number) => {
    try {
      await api.post(`/admin/lessons/${id}/reject/`);
      Alert.alert('Rejected', 'Lesson has been rejected.');
      refresh();
    } catch (err) {
      Alert.alert('Error', getErrorMessage(err));
    }
  };

  const handleComplete = async (id: number) => {
    try {
      await api.post(`/admin/lessons/${id}/complete/`);
      Alert.alert('Completed', 'Lesson marked complete and attendance checked.');
      refresh();
    } catch (err) {
      Alert.alert('Error', getErrorMessage(err));
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  const filtered = (data || []).filter(
    (l) =>
      l.student_name.toLowerCase().includes(search.toLowerCase()) ||
      l.lesson_item_name.toLowerCase().includes(search.toLowerCase())
  );

  const pending = filtered.filter((l) => !l.is_approved && l.submitted_by_student);
  const others = filtered.filter((l) => l.is_approved || !l.submitted_by_student);

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <TextInput
        placeholder="Search lessons..."
        placeholderTextColor={colors.textMuted}
        value={search}
        onChangeText={setSearch}
        style={[styles.search, { backgroundColor: colors.card, borderColor: colors.border, color: colors.text }]}
      />
      <FlatList
        data={[...pending, ...others]}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={filtered.length === 0 ? styles.emptyContainer : styles.list}
        ListEmptyComponent={<EmptyState icon="book-outline" title="No lessons found" />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <View style={styles.header}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.name, { color: colors.text }]}>{item.lesson_item_name}</Text>
                <Text style={[styles.sub, { color: colors.textMuted }]}>{item.student_name} - {item.student_number}</Text>
              </View>
              <Badge
                text={item.lesson_type}
                color={item.lesson_type === 'PRACTICAL' ? colors.primary : colors.info}
              />
            </View>
            <View style={styles.details}>
              <Text style={[styles.date, { color: colors.textMuted }]}>{item.date}</Text>
              <Badge
                text={item.is_approved ? 'Approved' : item.submitted_by_student ? 'Pending' : item.status}
                color={item.is_approved ? colors.success : item.submitted_by_student ? colors.warning : colors.textMuted}
              />
            </View>
            {item.remarks ? (
              <Text style={[styles.remarks, { color: colors.textMuted }]}>{item.remarks}</Text>
            ) : null}
            {item.submitted_by_student && !item.is_approved && (
              <View style={styles.actions}>
                <Button title="Approve" variant="primary" onPress={() => handleApprove(item.id)} style={styles.actionBtn} />
                <Button title="Reject" variant="danger" onPress={() => handleReject(item.id)} style={styles.actionBtn} />
              </View>
            )}
            {(!item.submitted_by_student || item.is_approved) && item.status !== 'COMPLETED' && (
              <View style={styles.actions}>
                <Button title="Mark Completed" variant="primary" onPress={() => handleComplete(item.id)} icon="checkmark-circle-outline" style={styles.actionBtn} />
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
    details: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.sm },
    date: { fontSize: 12, flex: 1 },
    remarks: { fontSize: 12, marginTop: spacing.sm, fontStyle: 'italic' },
    actions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
    actionBtn: { flex: 1, height: 40 },
  });
}
