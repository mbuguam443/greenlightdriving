import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useState, useMemo } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, FormInput } from '../../components/ui';
import { useAuth, getErrorMessage } from '../../context/AuthContext';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { AuthStackParamList } from '../../navigation/types';
import { radius, spacing } from '../../theme/colors';

type Props = NativeStackScreenProps<AuthStackParamList, 'Register'>;

export default function RegisterScreen({ navigation }: Props) {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { register } = useAuth();
  const [first, setFirst] = useState('');
  const [last, setLast] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRegister = async () => {
    if (!first.trim() || !last.trim() || !email.trim() || !password) {
      setError('Please fill in all required fields.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await register({
        first_name: first.trim(),
        last_name: last.trim(),
        email: email.trim(),
        phone: phone.trim(),
        password,
      });
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to create your account.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
          <Text style={styles.title}>Create account</Text>
          <Text style={styles.subtitle}>
            Register to apply for admission and track your training
          </Text>

          <View style={styles.formCard}>
            {error ? <Text style={styles.error}>{error}</Text> : null}

            <View style={styles.row}>
              <View style={styles.rowItem}>
                <FormInput label="First name" value={first} onChangeText={setFirst} placeholder="Jane" />
              </View>
              <View style={styles.rowItem}>
                <FormInput label="Last name" value={last} onChangeText={setLast} placeholder="Doe" />
              </View>
            </View>
            <FormInput
              label="Email"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
              placeholder="you@example.com"
            />
            <FormInput
              label="Phone"
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
              placeholder="07XXXXXXXX"
            />
            <FormInput
              label="Password"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              placeholder="Minimum 6 characters"
            />

            <Button title="Create Account" onPress={handleRegister} loading={loading} icon="person-add-outline" />
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>Already have an account?</Text>
            <Pressable onPress={() => navigation.goBack()}>
              <Text style={styles.footerLink}>Log in</Text>
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}


function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.primary },
  container: { flexGrow: 1, justifyContent: 'center', padding: spacing.lg },
  title: { fontSize: 26, fontWeight: '800', color: colors.white },
  subtitle: { fontSize: 14, color: colors.white, opacity: 0.9, marginTop: 4, marginBottom: spacing.lg },
  formCard: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    padding: spacing.lg,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 5,
  },
  row: { flexDirection: 'row', gap: spacing.sm },
  rowItem: { flex: 1 },
  error: {
    color: colors.danger,
    fontSize: 13,
    marginBottom: spacing.md,
    backgroundColor: `${colors.danger}1A`,
    padding: spacing.sm,
    borderRadius: radius.sm,
    overflow: 'hidden',
  },
  footer: { flexDirection: 'row', justifyContent: 'center', marginTop: spacing.lg, gap: 4 },
  footerText: { color: colors.white, opacity: 0.9 },
  footerLink: { color: colors.yellow, fontWeight: '700' },
});
}
