import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect, useMemo } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Card, EmptyState, ErrorState, Loading } from '../../components/ui';
import { useApiData } from '../../hooks/useApiData';
import { colors, radius, spacing } from '../../theme/colors';
import { LessonsData } from '../../types';
import { formatDate } from '../../utils/format';

type ScheduleEntry = {
  date: string;
  label: string;
  practical: Array<{ name: string; status: string; instructor: string | null }>;
  theory: Array<{ name: string; status: string; instructor: string | null }>;
};

export default function ScheduleScreen() {
  const isFocused = useIsFocused();
  const { data, loading, error, refreshing, refresh } = useApiData<LessonsData>('/student/lessons/');

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  const grouped = useMemo<ScheduleEntry[]>(() => {
    if (!data) return [];
    const map = new Map<string, ScheduleEntry>();
    const keyFor = (d: string) => (d ? d.slice(0, 10) : 'unknown');
    for (const l of data.practical_lessons) {
      const k = keyFor(l.date);
      if (!map.has(k)) map.set(k, { date: l.date, label: l.date, practical: [], theory: [] });
      map.get(k)!.practical.push({ name: l.lesson_item_name, status: l.status, instructor: l.instructor_name });
    }
    for (const l of data.theory_lessons) {
      const k = keyFor(l.date);
      if (!map.has(k)) map.set(k, { date: l.date, label: l.date, practical: [], theory: [] });
      map.get(k)!.theory.push({ name: l.topic || l.lesson_item_name || 'Theory lesson', status: l.status, instructor: l.instructor_name });
    }
    return Array.from(map.values()).sort((a, b) => a.date.localeCompare(b.date));
  }, [data]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {loading ? (
        <Loading />
      ) : error && !data ? (
        <ErrorState message={error} onRetry={refresh} />
      ) : (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.content}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}
        >
          {grouped.length === 0 ? (
            <EmptyState icon="calendar-outline" title="No lessons scheduled" subtitle="Your timetable will appear here" />
          ) : (
            grouped.map((entry) => (
              <View key={entry.date} style={styles.dayBlock}>
                <Text style={styles.dayLabel}>{formatDate(entry.date)}</Text>
                {entry.practical.map((p, i) => (
                  <Card key={`p-${i}`} style={styles.entryCard}>
                    <View style={styles.iconWrap}>
                      <Ionicons name="car-sport-outline" size={18} color={colors.primary} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.entryName}>{p.name}</Text>
                      <Text style={styles.entryMeta}>Practical · {p.instructor ?? 'TBA'}</Text>
                    </View>
                    <Badge text={p.status} />
                  </Card>
                ))}
                {entry.theory.map((t, i) => (
                  <Card key={`t-${i}`} style={styles.entryCard}>
                    <View style={[styles.iconWrap, { backgroundColor: `${colors.info}1A` }]}>
                      <Ionicons name="book-outline" size={18} color={colors.info} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.entryName}>{t.name}</Text>
                      <Text style={styles.entryMeta}>Theory · {t.instructor ?? 'TBA'}</Text>
                    </View>
                    <Badge text={t.status} />
                  </Card>
                ))}
              </View>
            ))
          )}
          <View style={styles.spacer} />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  scroll: { flex: 1 },
  content: { padding: spacing.md },
  dayBlock: { marginBottom: spacing.md },
  dayLabel: { fontSize: 15, fontWeight: '800', color: colors.text, marginBottom: spacing.sm },
  entryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    marginBottom: spacing.sm,
    borderRadius: radius.md,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: `${colors.primary}1A`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  entryName: { fontSize: 14, fontWeight: '700', color: colors.text },
  entryMeta: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
  spacer: { height: spacing.lg },
});
