import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, FormInput, Loading, ErrorState } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';
import { api, getErrorMessage } from '../../services/apiClient';
import { useApiData } from '../../hooks/useApiData';
import { BranchOption, Course, CourseCategory, AdmissionAccess } from '../../types';
import { radius, spacing } from '../../theme/colors';

const PACKAGE_OPTIONS = [
  { value: 'FULL', label: 'Full Course' },
  { value: 'HALF', label: 'Half Course' },
  { value: 'TEST', label: 'Test Only' },
];

const SCHEDULE_OPTIONS = [
  { value: 'MORNING', label: 'Morning (8AM-12PM)' },
  { value: 'AFTERNOON', label: 'Afternoon (1PM-5PM)' },
  { value: 'EVENING', label: 'Evening (5PM-8PM)' },
  { value: 'WEEKEND', label: 'Weekend' },
];

const GENDER_OPTIONS = [
  { value: 'M', label: 'Male' },
  { value: 'F', label: 'Female' },
  { value: 'OTHER', label: 'Other' },
];

function SelectField({
  label,
  value,
  options,
  onChange,
  colors,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
  colors: any;
}) {
  const styles = makeStyles(colors);
  return (
    <View style={{ marginBottom: spacing.md }}>
      <Text style={[styles.selectLabel, { color: colors.text }]}>{label}</Text>
      <View style={styles.chipWrap}>
        {options.map((o) => {
          const active = value === o.value;
          return (
            <Pressable
              key={o.value}
              onPress={() => onChange(o.value)}
              style={[
                styles.chip,
                { borderColor: active ? colors.primary : colors.border, backgroundColor: active ? `${colors.primary}1A` : colors.card },
              ]}
            >
              <Text style={[styles.chipText, { color: active ? colors.primary : colors.text }]}>{o.label}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function AdmissionForm({ onDone, colors }: { onDone: () => void; colors: any }) {
  const { data: categories } = useApiData<CourseCategory[]>('/course-categories/', []);
  const { data: branches } = useApiData<BranchOption[]>('/branches/', []);

  const [categoryId, setCategoryId] = useState('');
  const [courseId, setCourseId] = useState('');
  const [branchId, setBranchId] = useState('');
  const [packageChoice, setPackageChoice] = useState('FULL');
  const [schedule, setSchedule] = useState('MORNING');
  const [gender, setGender] = useState('M');
  const [dob, setDob] = useState('');
  const [nationalId, setNationalId] = useState('');
  const [address, setAddress] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const selectedCategory = useMemo(
    () => categories?.find((c) => String(c.id) === categoryId),
    [categories, categoryId]
  );

  const { data: courses } = useApiData<Course[]>(
    selectedCategory ? `/courses/?category=${selectedCategory.slug}` : '/courses/',
    [selectedCategory?.slug]
  );

  // Reset the selected course when the category changes
  useEffect(() => {
    setCourseId('');
  }, [categoryId, setCourseId]);

  const handleSubmit = async () => {
    if (!categoryId || !courseId || !branchId) {
      setError('Please select a course category, course and branch.');
      return;
    }
    if (!nationalId.trim() || !address.trim()) {
      setError('Please provide your National ID and address.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      await api.post('/student/admissions/', {
        category: Number(categoryId),
        course: Number(courseId),
        branch: Number(branchId),
        package_choice: packageChoice,
        preferred_schedule: schedule,
        gender,
        date_of_birth: dob || null,
        national_id: nationalId.trim(),
        address: address.trim(),
      });
      Alert.alert('Submitted', 'Your admission application has been submitted. You will be contacted once it is reviewed.');
      onDone();
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to submit your application.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ScrollView
      contentContainerStyle={makeStyles(colors).formScroll}
      keyboardShouldPersistTaps="handled"
      keyboardDismissMode="on-drag"
    >
      <Card>
        <Text style={makeStyles(colors).cardTitle}>Apply for admission</Text>
        <Text style={makeStyles(colors).cardSubtitle}>Fill in your details to apply for a course.</Text>

        {error ? <Text style={[makeStyles(colors).error, { color: colors.danger }]}>{error}</Text> : null}

        <SelectField
          label="Course category"
          value={categoryId}
          onChange={setCategoryId}
          colors={colors}
          options={(categories || []).map((c) => ({ value: String(c.id), label: c.name }))}
        />

        <SelectField
          label="Course"
          value={courseId}
          onChange={setCourseId}
          colors={colors}
          options={(courses || []).map((c) => ({ value: String(c.id), label: c.name }))}
        />

        <SelectField
          label="Branch"
          value={branchId}
          onChange={setBranchId}
          colors={colors}
          options={(branches || []).map((b) => ({ value: String(b.id), label: b.name }))}
        />

        <SelectField
          label="Package"
          value={packageChoice}
          onChange={setPackageChoice}
          colors={colors}
          options={PACKAGE_OPTIONS}
        />

        <SelectField
          label="Preferred schedule"
          value={schedule}
          onChange={setSchedule}
          colors={colors}
          options={SCHEDULE_OPTIONS}
        />

        <SelectField
          label="Gender"
          value={gender}
          onChange={setGender}
          colors={colors}
          options={GENDER_OPTIONS}
        />

        <FormInput
          label="Date of birth (YYYY-MM-DD)"
          value={dob}
          onChangeText={setDob}
          placeholder="2000-01-01"
          autoCapitalize="none"
        />
        <FormInput
          label="National ID number"
          value={nationalId}
          onChangeText={setNationalId}
          placeholder="e.g. 12345678"
        />
        <FormInput
          label="Home address"
          value={address}
          onChangeText={setAddress}
          placeholder="Physical address"
          multiline
          numberOfLines={3}
          style={{ height: 80, textAlignVertical: 'top' }}
        />

        <Button title="Submit Application" onPress={handleSubmit} loading={submitting} icon="send-outline" />
      </Card>
    </ScrollView>
  );
}

function StatusView({
  title,
  subtitle,
  icon,
  color,
  colors,
}: {
  title: string;
  subtitle: string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  colors: any;
}) {
  const styles = makeStyles(colors);
  return (
    <View style={styles.statusContainer}>
      <View style={[styles.statusIcon, { backgroundColor: `${color}1A` }]}>
        <Ionicons name={icon} size={44} color={color} />
      </View>
      <Text style={[styles.statusTitle, { color: colors.text }]}>{title}</Text>
      <Text style={[styles.statusSubtitle, { color: colors.textMuted }]}>{subtitle}</Text>
    </View>
  );
}

function InfoRow({ label, value, colors, valueColor }: { label: string; value: string; colors: any; valueColor?: string }) {
  const styles = makeStyles(colors);
  return (
    <View style={styles.infoRow}>
      <Text style={[styles.infoLabel, { color: colors.textMuted }]}>{label}</Text>
      <Text style={[styles.infoValue, { color: valueColor || colors.text }]}>{value}</Text>
    </View>
  );
}

interface AdmissionGateScreenProps {
  data: AdmissionAccess | null;
  loading: boolean;
  error: string;
  refreshing: boolean;
  refresh: () => void;
}

export default function AdmissionGateScreen(props: AdmissionGateScreenProps) {
  const { data, loading, error, refreshing, refresh } = props;
  const { colors } = useTheme();
  const styles = makeStyles(colors);
  const { user } = useAuth();
  const [showForm, setShowForm] = useState(false);

  useFocusEffect(
    useCallback(() => {
      refresh();
    }, [refresh])
  );

  if (loading && !data) return <Loading />;
  if (error && !data) return <ErrorState message={error} onRetry={refresh} />;

  const level = data?.access_level || 'none';
  const admission = data?.admission;

  let content: React.ReactNode;

  if (level === 'granted') {
    content = <StatusView icon="checkmark-circle-outline" color={colors.success} title="You're all set" subtitle="Your admission is approved. Loading your portal..." colors={colors} />;
  } else if (showForm && !admission) {
    content = <AdmissionForm onDone={refresh} colors={colors} />;
  } else if (admission && (level === 'pending' || (level === 'none' && showForm))) {
    content = (
      <ScrollView contentContainerStyle={styles.statusScroll} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}>
        <StatusView
          icon="hourglass-outline"
          color={colors.warning}
          title="Admission Under Review"
          subtitle="Your application has been received and is being reviewed. Most services will unlock once your admission is approved."
          colors={colors}
        />
        <Card style={styles.statusCard}>
          <InfoRow label="Reference" value={admission.admission_number || '—'} colors={colors} />
          <InfoRow label="Status" value="Pending" colors={colors} valueColor={colors.warning} />
          {admission.course_name ? <InfoRow label="Course" value={admission.course_name} colors={colors} /> : null}
          {admission.branch_name ? <InfoRow label="Branch" value={admission.branch_name} colors={colors} /> : null}
        </Card>
      </ScrollView>
    );
  } else if (level === 'rejected') {
    content = (
      <ScrollView contentContainerStyle={styles.statusScroll} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}>
        <StatusView
          icon="close-circle-outline"
          color={colors.danger}
          title="Application Not Approved"
          subtitle="Your admission application was not approved. Please contact the school for more information."
          colors={colors}
        />
        <Button title="Refresh" variant="outline" onPress={refresh} style={styles.retryBtn} />
      </ScrollView>
    );
  } else {
    content = (
      <ScrollView contentContainerStyle={styles.statusScroll} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}>
        <StatusView
          icon="document-text-outline"
          color={colors.primary}
          title="Apply for Admission"
          subtitle="You need to submit your admission application to unlock your student portal."
          colors={colors}
        />
        <Button title="Apply Now" onPress={() => setShowForm(true)} icon="create-outline" style={styles.retryBtn} />
      </ScrollView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.header}>
          <Text style={styles.hello}>Hello{user?.first_name ? `, ${user.first_name}` : ''}</Text>
        </View>
        {content}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function makeStyles(colors: ReturnType<typeof useTheme>['colors']) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: colors.background },
    header: { padding: spacing.md, paddingBottom: spacing.sm },
    hello: { fontSize: 18, fontWeight: '700', color: colors.text },
    formScroll: { padding: spacing.md, paddingBottom: spacing.xl },
    statusScroll: { flexGrow: 1, padding: spacing.lg },
    statusContainer: { alignItems: 'center', justifyContent: 'center', paddingVertical: spacing.xl, paddingHorizontal: spacing.lg, flex: 1 },
    statusIcon: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md },
    statusTitle: { fontSize: 20, fontWeight: '800', textAlign: 'center' },
    statusSubtitle: { fontSize: 14, textAlign: 'center', marginTop: spacing.sm, lineHeight: 20 },
    statusCard: { marginTop: spacing.md },
    infoRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
    infoLabel: { fontSize: 13 },
    infoValue: { fontSize: 13, fontWeight: '600' },
    cardTitle: { fontSize: 18, fontWeight: '800', color: colors.text },
    cardSubtitle: { fontSize: 13, color: colors.textMuted, marginTop: 2, marginBottom: spacing.sm },
    selectLabel: { fontSize: 13, fontWeight: '600', marginBottom: 6 },
    chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
    chip: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderRadius: radius.pill, borderWidth: 1.5 },
    chipText: { fontSize: 12, fontWeight: '600' },
    error: {
      fontSize: 13,
      marginBottom: spacing.md,
      backgroundColor: `${colors.danger}1A`,
      padding: spacing.sm,
      borderRadius: radius.sm,
      overflow: 'hidden',
    },
    retryBtn: { alignSelf: 'center', minWidth: 200, marginTop: spacing.lg },
  });
}
