import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useState } from 'react';
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
import { AuthStackParamList } from '../../navigation/types';
import { colors, radius, spacing } from '../../theme/colors';

type Props = NativeStackScreenProps<AuthStackParamList, 'Login'>;

export default function LoginScreen({ navigation }: Props) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      setError('Please enter your email and password.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await login(email.trim(), password);
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to log in.'));
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
          <View style={styles.brand}>
            <View style={styles.logo}>
              <Ionicons name="car-sport" size={40} color={colors.white} />
            </View>
            <Text style={styles.brandName}>Green Light</Text>
            <Text style={styles.brandTagline}>Defensive Driving School</Text>
            <Text style={styles.brandSlogan}>Drive Safe, Drive Smart</Text>
          </View>

          <View style={styles.formCard}>
            <Text style={styles.formTitle}>Welcome back</Text>
            <Text style={styles.formSubtitle}>Log in to access your student portal</Text>

            {error ? <Text style={styles.error}>{error}</Text> : null}

            <FormInput
              label="Email"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
              placeholder="you@example.com"
            />
            <FormInput
              label="Password"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              placeholder="Your password"
              onSubmitEditing={handleLogin}
            />

            <Button title="Log In" onPress={handleLogin} loading={loading} icon="log-in-outline" />
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>Don't have an account?</Text>
            <Pressable onPress={() => navigation.navigate('Register')}>
              <Text style={styles.footerLink}>Create an account</Text>
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.primary },
  container: { flexGrow: 1, justifyContent: 'center', padding: spacing.lg },
  brand: { alignItems: 'center', marginBottom: spacing.xl },
  logo: {
    width: 76,
    height: 76,
    borderRadius: 22,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  brandName: { fontSize: 26, fontWeight: '800', color: colors.white },
  brandTagline: { fontSize: 14, color: colors.white, opacity: 0.9, marginTop: 2 },
  brandSlogan: { fontSize: 12, color: colors.yellow, marginTop: 4, fontWeight: '600' },
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
  formTitle: { fontSize: 20, fontWeight: '800', color: colors.text },
  formSubtitle: { fontSize: 13, color: colors.textMuted, marginBottom: spacing.lg, marginTop: 2 },
  error: {
    color: colors.danger,
    fontSize: 13,
    marginBottom: spacing.md,
    backgroundColor: `${colors.danger}1A`,
    padding: spacing.sm,
    borderRadius: radius.sm,
    overflow: 'hidden',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: spacing.lg,
    gap: 4,
  },
  footerText: { color: colors.white, opacity: 0.9 },
  footerLink: { color: colors.yellow, fontWeight: '700' },
});
