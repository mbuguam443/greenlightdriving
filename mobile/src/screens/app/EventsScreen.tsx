import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect, useMemo } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Card, EmptyState, ErrorState, Loading, SectionTitle } from '../../components/ui';
import { useApiData } from '../../hooks/useApiData';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { radius, spacing } from '../../theme/colors';
import { EventItem } from '../../types';
import { formatDate, formatTime } from '../../utils/format';

interface EventsData {
  upcoming_events: EventItem[];
  past_events: EventItem[];
}

export default function EventsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const isFocused = useIsFocused();
  const { data, loading, error, refreshing, refresh } = useApiData<EventsData>('/student/events/');

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  const renderEvent = (e: EventItem) => (
    <Card key={e.id} style={[styles.card, e.is_important ? styles.importantCard : undefined]}>
      <View style={styles.header}>
        <View style={styles.dateBox}>
          <Text style={styles.dateDay}>{new Date(e.event_date).getDate()}</Text>
          <Text style={styles.dateMonth}>
            {new Date(e.event_date).toLocaleString('en-KE', { month: 'short' }).toUpperCase()}
          </Text>
        </View>
        <View style={{ flex: 1 }}>
          <View style={styles.titleRow}>
            <Text style={styles.title}>{e.title}</Text>
            {e.is_important ? <Badge text="Important" color={colors.danger} /> : null}
          </View>
          <Text style={styles.meta}>
            {formatDate(e.event_date)}
            {e.event_time ? ` · ${formatTime(e.event_time)}` : ''}
          </Text>
          <Text style={styles.meta}>{e.location || e.branch_name || 'Green Light Driving School'}</Text>
        </View>
      </View>
      {e.description ? <Text style={styles.description}>{e.description}</Text> : null}
    </Card>
  );

  const upcoming = data?.upcoming_events ?? [];
  const past = data?.past_events ?? [];

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
          <SectionTitle title="Upcoming events" />
          {upcoming.length === 0 ? (
            <EmptyState icon="megaphone-outline" title="No upcoming events" subtitle="Check back later for the latest events" />
          ) : (
            upcoming.map(renderEvent)
          )}

          {past.length > 0 ? (
            <>
              <SectionTitle title="Past events" />
              {past.map(renderEvent)}
            </>
          ) : null}
          <View style={styles.spacer} />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}


function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  scroll: { flex: 1 },
  content: { padding: spacing.md },
  card: { marginBottom: spacing.sm },
  importantCard: { borderWidth: 1, borderColor: colors.red },
  header: { flexDirection: 'row', gap: spacing.sm },
  dateBox: {
    width: 48,
    height: 52,
    borderRadius: radius.sm,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dateDay: { color: colors.white, fontSize: 18, fontWeight: '800' },
  dateMonth: { color: colors.white, fontSize: 10, fontWeight: '700' },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  title: { fontSize: 14, fontWeight: '700', color: colors.text, flexShrink: 1 },
  meta: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
  description: { fontSize: 13, color: colors.text, marginTop: spacing.sm },
  spacer: { height: spacing.lg },
});
}
