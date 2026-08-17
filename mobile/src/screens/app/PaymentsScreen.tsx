import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Button, Card, EmptyState, ErrorState, FormInput, Loading, SectionTitle } from '../../components/ui';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { colors, radius, spacing } from '../../theme/colors';
import { PaymentsData } from '../../types';
import { formatDate, formatKES } from '../../utils/format';

export default function PaymentsScreen() {
  const isFocused = useIsFocused();
  const { data, loading, error, refreshing, refresh } = useApiData<PaymentsData>('/student/payments/');
  const [phone, setPhone] = useState('');
  const [amount, setAmount] = useState('');
  const [sending, setSending] = useState(false);
  const [formError, setFormError] = useState('');
  const [pendingTransactionId, setPendingTransactionId] = useState<number | null>(null);

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  useEffect(() => {
    if (!isFocused || pendingTransactionId === null) return;
    const timer = setInterval(() => refresh(), 3000);
    return () => clearInterval(timer);
  }, [isFocused, pendingTransactionId, refresh]);

  useEffect(() => {
    if (pendingTransactionId === null || !data) return;
    const transaction = data.mpesa_transactions.find((item) => item.id === pendingTransactionId);
    if (transaction && transaction.status !== 'PENDING') setPendingTransactionId(null);
  }, [data, pendingTransactionId]);

  const sendMpesa = async () => {
    setFormError('');
    const clean = phone.replace(/[^\d]/g, '');
    if (clean.length < 9) {
      setFormError('Enter a valid Safaricom phone number.');
      return;
    }
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) {
      setFormError('Enter a valid amount greater than zero.');
      return;
    }
    setSending(true);
    try {
      const { data: res } = await api.post<{ detail: string; transaction_id: number }>('/student/mpesa/initiate/', {
        phone_number: clean,
        amount: amt,
      });
      setPendingTransactionId(res.transaction_id);
      Alert.alert('M-Pesa Request Sent', res.detail);
      refresh();
    } catch (err) {
      Alert.alert('M-Pesa Failed', getErrorMessage(err));
    } finally {
      setSending(false);
    }
  };

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
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}
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
              <Text style={styles.hint}>
                You'll receive an STK push on your phone. Enter 254XXXXXXXXX format.
              </Text>
              <FormInput
                label="M-Pesa phone number"
                value={phone}
                onChangeText={setPhone}
                placeholder="2547XXXXXXXX"
                keyboardType="phone-pad"
              />
              <FormInput
                label="Amount (KES)"
                value={amount}
                onChangeText={setAmount}
                placeholder="0"
                keyboardType="numeric"
              />
              {formError ? <Text style={styles.errorText}>{formError}</Text> : null}
              <Button
                title={sending ? 'Sending STK push...' : 'Send M-Pesa Request'}
                icon="logo-usd"
                loading={sending}
                onPress={sendMpesa}
              />
            </Card>

            <SectionTitle title="Payment history" />
            {pendingTransactionId !== null ? (
              <Card style={styles.progressCard}>
                <View style={styles.paymentRow}>
                  <Ionicons name="time-outline" size={22} color={colors.warning} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.progressTitle}>Waiting for M-Pesa confirmation</Text>
                    <Text style={styles.paymentMeta}>Complete the prompt on your phone. This screen updates automatically.</Text>
                  </View>
                </View>
              </Card>
            ) : null}
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
                      color={p.status.toLowerCase() === 'completed' ? colors.success : p.status.toLowerCase() === 'pending' ? colors.warning : colors.danger}
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
                      <Badge text={t.status} color={t.status.toLowerCase() === 'success' || t.status.toLowerCase() === 'completed' ? colors.success : t.status.toLowerCase() === 'pending' ? colors.warning : colors.danger} />
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

const styles = StyleSheet.create({
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
  summaryLabel: { color: colors.white, opacity: 0.8, fontSize: 11, fontWeight: '600' },
  summaryValue: { color: colors.yellow, fontSize: 17, fontWeight: '800', marginTop: 4 },
  summaryPaid: { color: colors.white, fontSize: 15, fontWeight: '700', marginTop: 4 },
  summaryTotal: { color: colors.white, fontSize: 13, fontWeight: '600', marginTop: 4 },
  hint: { fontSize: 13, color: colors.textMuted, marginBottom: spacing.md },
  errorText: { color: colors.danger, fontSize: 13, marginBottom: spacing.sm },
  paymentCard: { marginBottom: spacing.sm },
  progressCard: { marginBottom: spacing.sm, borderColor: colors.warning, borderWidth: 1 },
  progressTitle: { fontSize: 14, fontWeight: '700', color: colors.text },
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
