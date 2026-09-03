import React, { useMemo, useState } from 'react';
import {
  Alert,
  FlatList,
  Pressable,
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
import { PaymentRecord, StudentRecord } from '../../types';
import { radius, spacing } from '../../theme/colors';

const METHODS = [
  { value: 'CASH', label: 'Cash' },
  { value: 'MPESA', label: 'M-Pesa' },
  { value: 'BANK', label: 'Bank' },
  { value: 'CHEQUE', label: 'Cheque' },
];

function Chip({
  label,
  active,
  onPress,
  colors,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
  colors: any;
}) {
  const styles = makeStyles(colors);
  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.chip,
        { borderColor: active ? colors.primary : colors.border, backgroundColor: active ? `${colors.primary}1A` : colors.card },
      ]}
    >
      <Text style={[styles.chipText, { color: active ? colors.primary : colors.text }]}>{label}</Text>
    </Pressable>
  );
}

function RecordPaymentForm({ onDone, colors }: { onDone: () => void; colors: any }) {
  const styles = makeStyles(colors);
  const { data: students } = useApiData<StudentRecord[]>('/admin/students/', []);
  const [studentId, setStudentId] = useState<number | null>(null);
  const [method, setMethod] = useState<string>('CASH');
  const [amount, setAmount] = useState('');
  const [reference, setReference] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!studentId) {
      setError('Please select a student.');
      return;
    }
    const parsed = Number(amount);
    if (!amount || isNaN(parsed) || parsed <= 0) {
      setError('Please enter a valid amount greater than zero.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      await api.post('/admin/payments/', {
        student: studentId,
        amount: parsed,
        method,
        reference_number: reference.trim(),
        description: description.trim(),
        status: 'COMPLETED',
      });
      Alert.alert('Recorded', 'Payment recorded successfully.');
      onDone();
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to record the payment.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card style={styles.formCard}>
      <Text style={[styles.formTitle, { color: colors.text }]}>Record Payment</Text>

      {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}

      <Text style={[styles.fieldLabel, { color: colors.text }]}>Student</Text>
      <View style={styles.chipWrap}>
        {(students || []).map((s) => (
          <Chip
            key={s.id}
            label={`${s.full_name} · ${s.student_number}`}
            active={studentId === s.id}
            onPress={() => setStudentId(s.id)}
            colors={colors}
          />
        ))}
        {!students || students.length === 0 ? (
          <Text style={[styles.hint, { color: colors.textMuted }]}>No students available.</Text>
        ) : null}
      </View>

      <Text style={[styles.fieldLabel, { color: colors.text }]}>Payment method</Text>
      <View style={styles.chipWrap}>
        {METHODS.map((m) => (
          <Chip key={m.value} label={m.label} active={method === m.value} onPress={() => setMethod(m.value)} colors={colors} />
        ))}
      </View>

      <FormInput
        label="Amount (KES)"
        value={amount}
        onChangeText={setAmount}
        placeholder="e.g. 5000"
        keyboardType="numeric"
      />
      <FormInput
        label="Reference number"
        value={reference}
        onChangeText={setReference}
        placeholder="M-Pesa code, cheque no., etc. (optional)"
      />
      <FormInput
        label="Description"
        value={description}
        onChangeText={setDescription}
        placeholder="Note (optional)"
        multiline
        numberOfLines={2}
        style={{ height: 60, textAlignVertical: 'top' }}
      />

      <Button title="Record Payment" onPress={handleSubmit} loading={submitting} icon="checkmark-circle-outline" />
    </Card>
  );
}

export default function PaymentsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<PaymentRecord[]>('/admin/payments/');
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  const filtered = (data || []).filter(
    (p) =>
      p.student_name.toLowerCase().includes(search.toLowerCase()) ||
      p.receipt_number.toLowerCase().includes(search.toLowerCase())
  );

  const header = (
    <View>
      <Button
        title={showForm ? 'Cancel' : 'Record Payment'}
        variant={showForm ? 'outline' : 'primary'}
        onPress={() => setShowForm(!showForm)}
        icon={showForm ? 'close-outline' : 'add-circle-outline'}
        style={styles.recordBtn}
      />
      {showForm ? (
        <RecordPaymentForm onDone={() => { setShowForm(false); refresh(); }} colors={colors} />
      ) : (
        <TextInput
          placeholder="Search payments..."
          placeholderTextColor={colors.textMuted}
          value={search}
          onChangeText={setSearch}
          style={[styles.search, { backgroundColor: colors.card, borderColor: colors.border, color: colors.text }]}
        />
      )}
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FlatList
        data={filtered}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={filtered.length === 0 ? styles.emptyContainer : styles.list}
        ListHeaderComponent={header}
        ListEmptyComponent={
          showForm ? null : <EmptyState icon="card-outline" title="No payments found" />
        }
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
              <Badge text={item.status_display} color={item.status === 'COMPLETED' ? colors.success : colors.warning} />
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
    recordBtn: { margin: spacing.md, marginBottom: spacing.sm },
    formCard: { marginHorizontal: spacing.md, marginBottom: spacing.md },
    formTitle: { fontSize: 18, fontWeight: '800', marginBottom: spacing.sm },
    fieldLabel: { fontSize: 13, fontWeight: '600', marginTop: spacing.sm, marginBottom: 6 },
    chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.sm },
    chip: { paddingHorizontal: spacing.md, paddingVertical: 8, borderRadius: radius.pill, borderWidth: 1.5 },
    chipText: { fontSize: 12, fontWeight: '600' },
    hint: { fontSize: 12, fontStyle: 'italic' },
    error: {
      fontSize: 13,
      marginBottom: spacing.sm,
      backgroundColor: `${colors.danger}1A`,
      padding: spacing.sm,
      borderRadius: radius.sm,
      overflow: 'hidden',
    },
    search: {
      margin: spacing.md,
      borderWidth: 1,
      borderRadius: radius.md,
      paddingHorizontal: spacing.md,
      paddingVertical: 10,
      fontSize: 14,
    },
    list: { paddingHorizontal: spacing.md, paddingBottom: spacing.xl },
    emptyContainer: { flexGrow: 1 },
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
