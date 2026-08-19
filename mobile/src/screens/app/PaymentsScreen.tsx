import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect, useMemo } from 'react';
import { KeyboardAvoidingView, Platform, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Card, EmptyState, ErrorState, Loading, SectionTitle } from '../../components/ui';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { radius, spacing } from '../../theme/colors';
import { PaymentsData } from '../../types';
import { formatDate, formatKES } from '../../utils/format';

export default function PaymentsScreen() {
  const isFocused = useIsFocused();
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<PaymentsData>('/student/payments/');

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {loading ? (
        <Loading />
      ) : error && !data ? (
        <ErrorState message={error} onRetry={refresh} />
      ) : (
        <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
          <ScrollView
            style={styles.scroll}
            contentContainerStyle={styles.content}
            keyboardShouldPersistTaps="handled"
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
          >
            {data?.summary ? (
              <Card style={styles.summaryCard}>
                <View style={styles.summaryCol}>
                  <Text style={styles.summaryLabel}>Balance</Text>
                  <Text style={styles.summaryValue}>{formatKES(data.summary.balance)}</Text>
                </View>
                <View style={styles.summaryCol}>
                  <Text style={styles.summaryLabel}>Paid</Text>
                  <Text style={styles.summaryPaid}>{formatKES(data.summary.amount_paid)}</Text>
                </View>
                <View style={styles.summaryCol}>
                  <Text style={styles.summaryLabel}>Total fees</Text>
                  <Text style={styles.summaryTotal}>{formatKES(data.summary.total_fees)}</Text>
                </View>
              </Card>
            ) : null}

            <SectionTitle title="Pay with M-Pesa" />
            <Card>
              <Text style={styles.hint}>Pay manually using M-Pesa Till Number:</Text>
              <Text style={styles.tillNumber}>5181799</Text>
              <Text style={styles.hint}>Use your student number as the account/reference where requested.</Text>
            </Card>

            <SectionTitle title="Payment history" />
            {data && data.payments.length === 0 ? (
              <EmptyState icon="card-outline" title="No payments recorded" subtitle="Payments you make will show here" />
            ) : (
              data?.payments.map((p) => (
                <Card key={p.id} style={styles.paymentCard}>
                  <View style={styles.paymentRow}>
                    <View style={styles.iconWrap}>
                      <Ionicons name="receipt-outline" size={18} color={colors.primary} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.paymentAmount}>{formatKES(p.amount)}</Text>
                      <Text style={styles.paymentMeta}>
                        {p.method_display} · {p.receipt_number} · {formatDate(p.created_at)}
                      </Text>
                    </View>
                    <Badge
                      text={p.status_display}
                      color={
                        p.status.toLowerCase() === 'completed'
                          ? colors.success
                          : p.status.toLowerCase() === 'pending'
                            ? colors.warning
                            : colors.danger
                      }
                    />
                  </View>
                </Card>
              ))
            )}

            {data && data.mpesa_transactions.length > 0 ? (
              <>
                <SectionTitle title="M-Pesa transactions" />
                {data.mpesa_transactions.map((t) => (
                  <Card key={t.id} style={styles.paymentCard}>
                    <View style={styles.paymentRow}>
                      <View style={[styles.iconWrap, { backgroundColor: `${colors.success}1A` }]}>
                        <Ionicons name="logo-usd" size={18} color={colors.success} />
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.paymentAmount}>{formatKES(t.amount)}</Text>
                        <Text style={styles.paymentMeta}>
                          {t.phone_number} · {formatDate(t.created_at)}
                          {t.mpesa_receipt ? ` · ${t.mpesa_receipt}` : ''}
                        </Text>
                      </View>
                      <Badge
                        text={t.status}
                        color={
                          t.status.toLowerCase() === 'success' || t.status.toLowerCase() === 'completed'
                            ? colors.success
                            : t.status.toLowerCase() === 'pending'
                              ? colors.warning
                              : colors.danger
                        }
                      />
                    </View>
                  </Card>
                ))}
              </>
            ) : null}

            <View style={styles.spacer} />
          </ScrollView>
        </KeyboardAvoidingView>
      )}
    </SafeAreaView>
  );
}

function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: colors.background },
    scroll: { flex: 1 },
    content: { padding: spacing.md },
    summaryCard: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      backgroundColor: colors.primaryDark,
      marginBottom: spacing.sm,
    },
    summaryCol: { flex: 1 },
    summaryLabel: { color: colors.onPrimary, opacity: 0.8, fontSize: 11, fontWeight: '600' },
    summaryValue: { color: colors.yellow, fontSize: 17, fontWeight: '800', marginTop: 4 },
    summaryPaid: { color: colors.onPrimary, fontSize: 15, fontWeight: '700', marginTop: 4 },
    summaryTotal: { color: colors.onPrimary, fontSize: 13, fontWeight: '600', marginTop: 4 },
    hint: { fontSize: 13, color: colors.textMuted, marginBottom: spacing.md },
    tillNumber: { fontSize: 28, fontWeight: '800', color: colors.primary, letterSpacing: 2, marginBottom: spacing.sm },
    paymentCard: { marginBottom: spacing.sm },
    paymentRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
    iconWrap: {
      width: 36,
      height: 36,
      borderRadius: 10,
      backgroundColor: `${colors.primary}1A`,
      alignItems: 'center',
      justifyContent: 'center',
    },
    paymentAmount: { fontSize: 15, fontWeight: '700', color: colors.text },
    paymentMeta: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    spacer: { height: spacing.lg },
  });
}
