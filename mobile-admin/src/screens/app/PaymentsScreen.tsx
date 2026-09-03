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

import { Card, EmptyState, Loading, ErrorState, Badge, Button, FormInput } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { PaymentRecord } from '../../types';
import { radius, spacing } from '../../theme/colors';

export default function PaymentsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<PaymentRecord[]>('/admin/payments/');
  const [search, setSearch] = useState('');

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  const filtered = (data || []).filter(
    (p) =>
      p.student_name.toLowerCase().includes(search.toLowerCase()) ||
      p.receipt_number.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <TextInput
        placeholder="Search payments..."
        placeholderTextColor={colors.textMuted}
        value={search}
        onChangeText={setSearch}
        style={[styles.search, { backgroundColor: colors.card, borderColor: colors.border, color: colors.text }]}
      />
      <FlatList
        data={filtered}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={filtered.length === 0 ? styles.emptyContainer : styles.list}
        ListEmptyComponent={<EmptyState icon="card-outline" title="No payments found" />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <View style={styles.header}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.name, { color: colors.text }]}>{item.student_name}</Text>
                <Text style={[styles.sub, { color: colors.textMuted }]}>{item.receipt_number}</Text>
              </View>
              <Text style={[styles.amount, { color: colors.success }]}>KES {item.amount}</Text>
            </View>
            <View style={styles.details}>
              <Badge text={item.method_display} />
              <Badge text={item.status_display} color={item.status === 'CONFIRMED' ? colors.success : colors.warning} />
              <Text style={[styles.date, { color: colors.textMuted }]}>{item.created_at}</Text>
            </View>
            {item.description ? (
              <Text style={[styles.desc, { color: colors.textMuted }]}>{item.description}</Text>
            ) : null}
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
    amount: { fontSize: 16, fontWeight: '800' },
    details: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.sm, flexWrap: 'wrap' },
    date: { fontSize: 11, marginLeft: 'auto' },
    desc: { fontSize: 12, marginTop: spacing.sm },
  });
}
