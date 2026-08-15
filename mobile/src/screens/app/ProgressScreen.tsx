import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Card, EmptyState, ErrorState, Loading, ProgressBar, SectionTitle } from '../../components/ui';
import { useApiData } from '../../hooks/useApiData';
import { colors, radius, spacing } from '../../theme/colors';
import { NTSARecord } from '../../types';
import { formatDate } from '../../utils/format';

function statusTone(status: string): string {
  switch (status) {
    case 'PASSED':
      return colors.success;
    case 'FAILED':
      return colors.danger;
    case 'PENDING':
    case 'SCHEDULED':
      return colors.warning;
    default:
      return colors.info;
  }
}

function Stage({
  icon,
  title,
  status,
  date,
  detail,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  status: string;
  date?: string | null;
  detail?: string;
}) {
  const tone = statusTone(status);
  return (
    <Card style={styles.stageCard}>
      <View style={[styles.stageIcon, { backgroundColor: `${tone}1A` }]}>
        <Ionicons name={icon} size={20} color={tone} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.stageTitle}>{title}</Text>
        {detail ? <Text style={styles.stageDetail}>{detail}</Text> : null}
        {date ? <Text style={styles.stageDate}>{formatDate(date)}</Text> : null}
      </View>
      <Badge text={status} color={tone} />
    </Card>
  );
}

export default function ProgressScreen() {
  const isFocused = useIsFocused();
  const { data, loading, error, refreshing, refresh } = useApiData<NTSARecord | null>('/student/ntsa/');

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {loading ? (
        <Loading />
      ) : error && !data ? (
        <ErrorState message={error} onRetry={refresh} />
      ) : !data ? (
        <EmptyState
          icon="analytics-outline"
          title="No NTSA record yet"
          subtitle="Your NTSA progress will appear here once you begin your training"
        />
      ) : (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.content}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}
        >
          <Card style={styles.overallCard}>
            <View style={styles.overallHeader}>
              <Text style={styles.overallTitle}>Overall training progress</Text>
              <Text style={styles.overallPct}>{Math.round(data.overall_progress)}%</Text>
            </View>
            <ProgressBar value={data.overall_progress} />
          </Card>

          <SectionTitle title="Licensing journey" />
          <Stage
            icon="card-outline"
            title="Provisional Driving Licence (PDL)"
            status={data.pdl_status_display}
            date={data.pdl_date}
            detail={data.pdl_number ? `PDL No: ${data.pdl_number}` : undefined}
          />
          <Stage
            icon="book-outline"
            title="Theory exam"
            status={data.theory_exam_status_display}
            date={data.theory_exam_date}
            detail={data.theory_exam_score != null ? `Score: ${data.theory_exam_score}%` : undefined}
          />
          <Stage
            icon="car-sport-outline"
            title="Practical exam"
            status={data.practical_exam_status_display}
            date={data.practical_exam_date}
          />
          <Stage
            icon="trail-sign-outline"
            title="Driving test"
            status={data.driving_test_status_display}
            date={data.driving_test_date}
          />

          <SectionTitle title="Driving licence" />
          <Card style={styles.licenceCard}>
            <View style={styles.licenceHeader}>
              <View style={styles.licenceIcon}>
                <Ionicons name="shield-checkmark-outline" size={24} color={colors.white} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.licenceTitle}>Licence status</Text>
                <Badge
                  text={data.licence_issued ? 'Licence issued' : 'Not issued'}
                  color={data.licence_issued ? colors.success : colors.warning}
                  bg={data.licence_issued ? `${colors.success}1A` : `${colors.warning}1A`}
                />
              </View>
            </View>
            {data.licence_issued ? (
              <View style={styles.licenceMeta}>
                <Text style={styles.licenceNumber}>Licence No: {data.licence_number}</Text>
                <Text style={styles.licenceDates}>
                  Issued {formatDate(data.licence_issue_date)} · Expires {formatDate(data.licence_expiry_date)}
                </Text>
              </View>
            ) : null}
          </Card>

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
  overallCard: { backgroundColor: colors.primaryDark, marginBottom: spacing.sm },
  overallHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  overallTitle: { color: colors.white, fontSize: 14, fontWeight: '700' },
  overallPct: { color: colors.yellow, fontSize: 20, fontWeight: '800' },
  stageCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    marginBottom: spacing.sm,
    borderRadius: radius.md,
  },
  stageIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stageTitle: { fontSize: 14, fontWeight: '700', color: colors.text },
  stageDetail: { fontSize: 12, color: colors.text, marginTop: 2 },
  stageDate: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
  licenceCard: { backgroundColor: colors.primary },
  licenceHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  licenceIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  licenceTitle: { color: colors.white, fontSize: 14, fontWeight: '700', marginBottom: 6 },
  licenceMeta: { marginTop: spacing.md, borderTopWidth: 1, borderTopColor: `${colors.white}33`, paddingTop: spacing.sm },
  licenceNumber: { color: colors.white, fontSize: 14, fontWeight: '800' },
  licenceDates: { color: colors.white, opacity: 0.85, fontSize: 12, marginTop: 2 },
  spacer: { height: spacing.lg },
});
