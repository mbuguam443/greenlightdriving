import { Ionicons } from '@expo/vector-icons';
import { useIsFocused, useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Card, EmptyState, ErrorState, Loading } from '../../components/ui';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { HomeStackParamList } from '../../navigation/types';
import { radius, spacing } from '../../theme/colors';
import { AdminStudent, StudentsData } from '../../types';
import { formatKES } from '../../utils/format';

type Nav = NativeStackNavigationProp<HomeStackParamList, 'Dashboard'>;

export default function StudentsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const navigation = useNavigation<Nav>();
  const isFocused = useIsFocused();
  const [query, setQuery] = useState('');
  const [debounced, setDebounced] = useState('');
  const path = debounced ? `/admin/students/?q=${encodeURIComponent(debounced)}` : '/admin/students/';
  const { data, loading, error, refreshing, refresh } = useApiData<StudentsData>(path, [path]);

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query.trim()), 400);
    return () => clearTimeout(t);
  }, [query]);

  const renderStudent = (s: AdminStudent) => (
    <Pressable
      key={s.id}
      onPress={() => navigation.navigate('StudentDetail', { id: s.id, name: s.user.full_name })}
    >
      <Card style={styles.studentCard}>
        <View style={styles.row}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {`${s.user.first_name?.[0] ?? ''}${s.user.last_name?.[0] ?? ''}`.toUpperCase() || 'S'}
            </Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{s.user.full_name}</Text>
            <Text style={styles.meta}>
              {s.student_number} · {s.course_name}
            </Text>
            <Text style={styles.meta}>{s.user.phone || s.user.email}</Text>
          </View>
          <View style={styles.rightCol}>
            <Badge
              text={s.status}
              color={s.status === 'ACTIVE' ? colors.success : s.status === 'GRADUATED' ? colors.info : colors.danger}
            />
            <Text style={[styles.balance, parseFloat(s.balance) > 0 ? { color: colors.danger } : { color: colors.success }]}>
              {formatKES(s.balance)}
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
        </View>
      </Card>
    </Pressable>
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.searchWrap}>
        <View style={styles.searchBox}>
          <Ionicons name="search-outline" size={18} color={colors.textMuted} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search name, number, phone, email..."
            placeholderTextColor={colors.textMuted}
            value={query}
            onChangeText={setQuery}
            autoCapitalize="none"
          />
          {query ? (
            <Pressable onPress={() => setQuery('')}>
              <Ionicons name="close-circle" size={18} color={colors.textMuted} />
            </Pressable>
          ) : null}
        </View>
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
        ) : data && data.students.length === 0 ? (
          <EmptyState icon="people-outline" title="No students found" subtitle="Try a different search" />
        ) : (
          data?.students.map(renderStudent)
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
    searchWrap: { padding: spacing.md, paddingBottom: 0 },
    searchBox: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.sm,
      backgroundColor: colors.card,
      borderRadius: radius.md,
      paddingHorizontal: spacing.md,
      borderWidth: 1,
      borderColor: colors.border,
      height: 44,
    },
    searchInput: { flex: 1, fontSize: 14, color: colors.text, padding: 0 },
    content: { padding: spacing.md },
    studentCard: { marginBottom: spacing.sm },
    row: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
    avatar: {
      width: 42,
      height: 42,
      borderRadius: 21,
      backgroundColor: colors.primary,
      alignItems: 'center',
      justifyContent: 'center',
    },
    avatarText: { color: colors.onPrimary, fontSize: 15, fontWeight: '800' },
    name: { fontSize: 15, fontWeight: '700', color: colors.text },
    meta: { fontSize: 12, color: colors.textMuted, marginTop: 1 },
    rightCol: { alignItems: 'flex-end', gap: 4 },
    balance: { fontSize: 12, fontWeight: '700' },
    spacer: { height: spacing.lg },
  });
}
