import { Ionicons } from '@expo/vector-icons';
import React, { useEffect, useMemo, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Button, Card, ErrorState, FormInput, Loading, SectionTitle } from '../../components/ui';
import { useAuth, getErrorMessage } from '../../context/AuthContext';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { api } from '../../services/apiClient';
import { radius, spacing } from '../../theme/colors';

interface ProfileData {
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    full_name: string;
    phone: string;
    role: string;
    passport_photo: string | null;
    is_verified: boolean;
  };
}

export default function ProfileScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { logout } = useAuth();
  const { data, loading, error, refreshing, refresh, setData } = useApiData<ProfileData>('/admin/profile/');

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  useEffect(() => {
    if (data) {
      setFirstName(data.user.first_name ?? '');
      setLastName(data.user.last_name ?? '');
      setPhone(data.user.phone ?? '');
    }
  }, [data]);

  const save = async () => {
    setFormError('');
    if (!firstName.trim() || !lastName.trim()) {
      setFormError('First and last name are required.');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone: phone.trim(),
      };
      const { data: res } = await api.put<{ detail: string; user: ProfileData['user'] }>('/admin/profile/', payload);
      setData((prev) => (prev ? { ...prev, user: { ...prev.user, ...res.user } } : prev));
      Alert.alert('Profile updated', 'Your details have been saved.');
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    Alert.alert('Log out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log out', style: 'destructive', onPress: () => logout() },
    ]);
  };

  if (loading) return <Loading />;
  if (error && !data) return <ErrorState message={error} onRetry={refresh} />;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView style={styles.scroll} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Card style={styles.summaryCard}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {`${data?.user.first_name?.[0] ?? ''}${data?.user.last_name?.[0] ?? ''}`.toUpperCase() || 'A'}
              </Text>
            </View>
            <Text style={styles.fullName}>{data?.user.full_name}</Text>
            <View style={styles.badgeRow}>
              <Badge text={data?.user.role ?? 'STAFF'} />
            </View>
          </Card>

          <SectionTitle title="Personal details" />
          <Card>
            {formError ? <Text style={styles.errorText}>{formError}</Text> : null}
            <View style={styles.row}>
              <View style={styles.rowItem}>
                <FormInput label="First name" value={firstName} onChangeText={setFirstName} placeholder="Jane" />
              </View>
              <View style={styles.rowItem}>
                <FormInput label="Last name" value={lastName} onChangeText={setLastName} placeholder="Doe" />
              </View>
            </View>
            <FormInput label="Email" value={data?.user.email ?? ''} editable={false} />
            <FormInput label="Phone" value={phone} onChangeText={setPhone} keyboardType="phone-pad" placeholder="07XXXXXXXX" />

            <Button title="Save changes" icon="save-outline" loading={saving} onPress={save} />
          </Card>

          <Button
            title="Log out"
            variant="danger"
            icon="log-out-outline"
            style={styles.logout}
            onPress={handleLogout}
          />
          <View style={styles.spacer} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: colors.background },
    scroll: { flex: 1 },
    content: { padding: spacing.md },
    summaryCard: { alignItems: 'center', paddingVertical: spacing.lg, marginBottom: spacing.sm },
    avatar: {
      width: 72,
      height: 72,
      borderRadius: 36,
      backgroundColor: colors.primary,
      alignItems: 'center',
      justifyContent: 'center',
      marginBottom: spacing.sm,
    },
    avatarText: { color: colors.onPrimary, fontSize: 26, fontWeight: '800' },
    fullName: { fontSize: 18, fontWeight: '800', color: colors.text },
    badgeRow: { flexDirection: 'row', gap: 6, marginTop: spacing.sm },
    row: { flexDirection: 'row', gap: spacing.sm },
    rowItem: { flex: 1 },
    errorText: { color: colors.danger, fontSize: 13, marginBottom: spacing.sm },
    logout: { marginTop: spacing.lg },
    spacer: { height: spacing.lg },
  });
}
