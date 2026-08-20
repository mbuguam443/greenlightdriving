import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Modal, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Button, Card, EmptyState, ErrorState, FormInput, Loading, SectionTitle, StatCard } from '../../components/ui';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { radius, spacing } from '../../theme/colors';
import { AdminStudent, PaymentsData, StudentsData } from '../../types';
import { formatDate, formatKES } from '../../utils/format';

const METHODS = [
  { value: 'CASH', label: 'Cash' },
  { value: 'MPESA', label: 'M-Pesa' },
  { value: 'BANK', label: 'Bank Transfer' },
  { value: 'CHEQUE', label: 'Cheque' },
];

export default function PaymentsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const isFocused = useIsFocused();
  const { data, loading, error, refreshing, refresh } = useApiData<PaymentsData>('/admin/payments/');

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  const [modalOpen, setModalOpen] = useState(false);
  const [students, setStudents] = useState<AdminStudent[]>([]);
  const [studentQuery, setStudentQuery] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<AdminStudent | null>(null);
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('MPESA');
  const [reference, setReference] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const openModal = async () => {
    setModalOpen(true);
    setAmount('');
    setMethod('MPESA');
    setReference('');
    setDescription('');
    setFormError('');
    setSelectedStudent(null);
    setStudentQuery('');
    try {
      const { data: res } = await api.get<StudentsData>('/admin/students/?status=ACTIVE');
      setStudents(res.students);
    } catch {
      // students list will be empty; user can retry by reopening
    }
  };

  const filteredStudents = studentQuery.trim()
    ? students.filter(
        (s) =>
          s.user.full_name.toLowerCase().includes(studentQuery.toLowerCase()) ||
          s.student_number.toLowerCase().includes(studentQuery.toLowerCase())
      )
    : students;

  const save = async () => {
    if (!selectedStudent) {
      setFormError('Select a student.');
      return;
    }
    if (!amount || parseFloat(amount) <= 0) {
      setFormError('Enter a valid amount.');
      return;
    }
    setFormError('');
    setSaving(true);
    try {
      await api.post('/admin/payments/', {
        student: selectedStudent.id,
        amount: parseFloat(amount),
        method,
        reference_number: reference,
        description,
      });
      setModalOpen(false);
      Alert.alert('Payment recorded', `Receipt saved for ${selectedStudent.user.full_name}.`);
      refresh();
    } catch (err) {
      setFormError(getErrorMessage(err, 'Could not record the payment.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.headerRow}>
        <View style={{ flex: 1 }}>
          <StatCard label="Total collected" value={formatKES(data?.total_completed)} icon="cash-outline" />
        </View>
        <Pressable style={styles.recordBtn} onPress={openModal}>
          <Ionicons name="add" size={20} color={colors.onPrimary} />
          <Text style={styles.recordBtnText}>Record</Text>
        </Pressable>
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
        ) : data && data.payments.length === 0 ? (
          <EmptyState icon="card-outline" title="No payments" subtitle="Recorded payments will appear here" />
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
                  color={p.status === 'COMPLETED' ? colors.success : p.status === 'PENDING' ? colors.warning : colors.danger}
                />
              </View>
            </Card>
          ))
        )}
        <View style={styles.spacer} />
      </ScrollView>

      <Modal visible={modalOpen} transparent animationType="fade">
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Record payment</Text>

            {formError ? <Text style={styles.formError}>{formError}</Text> : null}

            {selectedStudent ? (
              <View style={styles.selectedRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.selectedName}>{selectedStudent.user.full_name}</Text>
                  <Text style={styles.selectedMeta}>
                    {selectedStudent.student_number} · Balance {formatKES(selectedStudent.balance)}
                  </Text>
                </View>
                <Pressable onPress={() => setSelectedStudent(null)}>
                  <Ionicons name="close-circle" size={22} color={colors.danger} />
                </Pressable>
              </View>
            ) : (
              <>
                <Text style={styles.fieldLabel}>Student</Text>
                <FormInput
                  placeholder="Search student..."
                  value={studentQuery}
                  onChangeText={setStudentQuery}
                  autoCapitalize="none"
                />
                <View style={styles.studentList}>
                  <ScrollView style={{ maxHeight: 160 }} keyboardShouldPersistTaps="handled">
                    {filteredStudents.slice(0, 20).map((s) => (
                      <Pressable
                        key={s.id}
                        style={styles.studentOption}
                        onPress={() => setSelectedStudent(s)}
                      >
                        <Text style={styles.studentOptionName}>{s.user.full_name}</Text>
                        <Text style={styles.studentOptionMeta}>
                          {s.student_number} · Bal {formatKES(s.balance)}
                        </Text>
                      </Pressable>
                    ))}
                    {filteredStudents.length === 0 ? (
                      <Text style={styles.noStudents}>No students found</Text>
                    ) : null}
                  </ScrollView>
                </View>
              </>
            )}

            <Text style={styles.fieldLabel}>Amount (KES)</Text>
            <FormInput value={amount} onChangeText={setAmount} keyboardType="numeric" placeholder="0" />

            <Text style={styles.fieldLabel}>Method</Text>
            <View style={styles.methodRow}>
              {METHODS.map((m) => (
                <Pressable
                  key={m.value}
                  style={[styles.methodBtn, method === m.value && styles.methodBtnActive]}
                  onPress={() => setMethod(m.value)}
                >
                  <Text style={[styles.methodBtnText, method === m.value && styles.methodBtnTextActive]}>
                    {m.label}
                  </Text>
                </Pressable>
              ))}
            </View>

            <Text style={styles.fieldLabel}>Reference (optional)</Text>
            <FormInput value={reference} onChangeText={setReference} placeholder="M-Pesa code / cheque no" />

            <Text style={styles.fieldLabel}>Description (optional)</Text>
            <FormInput value={description} onChangeText={setDescription} placeholder="Fee payment" />

            <View style={styles.modalActions}>
              <Button title="Cancel" variant="ghost" onPress={() => setModalOpen(false)} style={{ flex: 1 }} />
              <Button title="Save payment" loading={saving} onPress={save} style={{ flex: 1 }} />
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: colors.background },
    scroll: { flex: 1 },
    headerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, padding: spacing.md, paddingBottom: 0 },
    recordBtn: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 4,
      backgroundColor: colors.primary,
      borderRadius: radius.md,
      paddingHorizontal: spacing.md,
      height: 48,
    },
    recordBtnText: { color: colors.onPrimary, fontWeight: '700', fontSize: 14 },
    content: { padding: spacing.md },
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
    modalBackdrop: {
      flex: 1,
      backgroundColor: 'rgba(0,0,0,0.5)',
      alignItems: 'center',
      justifyContent: 'center',
      padding: spacing.lg,
    },
    modalCard: {
      width: '100%',
      backgroundColor: colors.card,
      borderRadius: radius.lg,
      padding: spacing.lg,
      maxHeight: '90%',
    },
    modalTitle: { fontSize: 18, fontWeight: '800', color: colors.text, marginBottom: spacing.sm },
    formError: { color: colors.danger, fontSize: 13, marginBottom: spacing.sm },
    fieldLabel: { fontSize: 13, fontWeight: '600', color: colors.text, marginBottom: 6, marginTop: 6 },
    selectedRow: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: `${colors.primary}12`,
      borderRadius: radius.md,
      padding: spacing.sm,
      marginBottom: spacing.sm,
    },
    selectedName: { fontSize: 14, fontWeight: '700', color: colors.text },
    selectedMeta: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    studentList: {
      borderWidth: 1,
      borderColor: colors.border,
      borderRadius: radius.md,
      marginBottom: spacing.sm,
    },
    studentOption: { padding: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border },
    studentOptionName: { fontSize: 14, fontWeight: '600', color: colors.text },
    studentOptionMeta: { fontSize: 12, color: colors.textMuted, marginTop: 1 },
    noStudents: { padding: spacing.sm, fontSize: 13, color: colors.textMuted, textAlign: 'center' },
    methodRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
    methodBtn: {
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: radius.pill,
      borderWidth: 1,
      borderColor: colors.border,
      backgroundColor: colors.background,
    },
    methodBtnActive: { backgroundColor: colors.primary, borderColor: colors.primary },
    methodBtnText: { fontSize: 12, fontWeight: '600', color: colors.text },
    methodBtnTextActive: { color: colors.onPrimary },
    modalActions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
  });
}
