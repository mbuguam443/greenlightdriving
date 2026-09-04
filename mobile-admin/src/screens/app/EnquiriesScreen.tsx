import React, { useMemo, useState } from 'react';
import {
  Alert,
  FlatList,
  Linking,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Card, EmptyState, Loading, ErrorState, Badge, Button } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { EnquiryRecord } from '../../types';
import { radius, spacing } from '../../theme/colors';

export default function EnquiriesScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<EnquiryRecord[]>('/admin/inquiries/');

  const call = (phone: string) => {
    Linking.openURL(`tel:${phone}`).catch(() => Alert.alert('Error', 'Could not open the dialer.'));
  };

  const act = async (id: number, action: string, success: string) => {
    try {
      await api.post(`/admin/inquiries/${id}/${action}/`);
      Alert.alert('Done', success);
      refresh();
    } catch (err) {
      Alert.alert('Error', getErrorMessage(err));
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FlatList
        data={data || []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={!data || data.length === 0 ? styles.emptyContainer : styles.list}
        ListEmptyComponent={<EmptyState icon="call-outline" title="No enquiries yet" />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <View style={styles.header}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.name, { color: colors.text }]}>{item.name}</Text>
                <Text style={[styles.sub, { color: colors.textMuted }]}>{item.course_name || 'Course not specified'}</Text>
              </View>
              <Badge
                text={item.converted ? 'Converted' : item.followed_up ? 'Followed up' : 'New'}
                color={item.converted ? colors.success : item.followed_up ? colors.info : colors.danger}
              />
            </View>

            <Pressable onPress={() => call(item.phone)} style={styles.phoneRow}>
              <Text style={[styles.phone, { color: colors.primary }]}>{item.phone}</Text>
              <Text style={[styles.callHint, { color: colors.primary }]}>Tap to call</Text>
            </Pressable>

            {item.email ? <Text style={[styles.sub, { color: colors.textMuted }]}>{item.email}</Text> : null}
            {item.feedback ? <Text style={[styles.feedback, { color: colors.textMuted }]}>{item.feedback}</Text> : null}

            <Text style={[styles.date, { color: colors.textMuted }]}>{item.created_at}</Text>
            <View style={styles.actions}>
              <Button
                title={item.followed_up ? 'Unmark follow-up' : 'Mark followed up'}
                variant={item.followed_up ? 'ghost' : 'outline'}
                onPress={() => act(item.id, 'toggle-follow-up', item.followed_up ? 'Follow-up removed.' : 'Marked as followed up.')}
                icon="checkmark-done-outline"
                style={styles.actionBtn}
              />
              <Button
                title={item.converted ? 'Unconvert' : 'Convert'}
                variant={item.converted ? 'ghost' : 'outline'}
                onPress={() => act(item.id, 'toggle-convert', item.converted ? 'Conversion removed.' : 'Marked as converted.')}
                icon="person-add-outline"
                style={styles.actionBtn}
              />
              <Button
                title="Delete"
                variant="danger"
                onPress={() => {
                  Alert.alert('Delete enquiry', `Delete enquiry from ${item.name}?`, [
                    { text: 'Cancel', style: 'cancel' },
                    { text: 'Delete', style: 'destructive', onPress: () => act(item.id, 'delete', 'Enquiry deleted.') },
                  ]);
                }}
                icon="trash-outline"
                style={styles.actionBtn}
              />
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
    list: { paddingHorizontal: spacing.md, paddingBottom: spacing.xl },
    emptyContainer: { flex: 1 },
    card: { marginBottom: spacing.sm },
    header: { flexDirection: 'row', alignItems: 'flex-start' },
    name: { fontSize: 15, fontWeight: '700' },
    sub: { fontSize: 12, marginTop: 2 },
    phoneRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.sm },
    phone: { fontSize: 15, fontWeight: '700' },
    callHint: { fontSize: 11, fontWeight: '600' },
    feedback: { fontSize: 12, marginTop: spacing.sm, fontStyle: 'italic' },
    date: { fontSize: 11, marginTop: spacing.sm },
    actions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
    actionBtn: { flex: 1, height: 40, paddingHorizontal: 0 },
  });
}
