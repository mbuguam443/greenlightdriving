import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useMemo, useState } from 'react';
import {
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Button, FormInput } from '../../components/ui';
import { useAuth, getErrorMessage } from '../../context/AuthContext';
import { ThemeColors, useTheme } from '../../context/ThemeContext';
import { AuthStackParamList } from '../../navigation/types';
import { radius, spacing } from '../../theme/colors';

type Props = NativeStackScreenProps<AuthStackParamList, 'Login'>;

export default function LoginScreen({}: Props) {
  const { login } = useAuth();
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const insets = useSafeAreaInsets();
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
    <View style={[styles.safe, { paddingTop: insets.top }]}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? insets.top : 0}
      >
        <ScrollView
          contentContainerStyle={[styles.container, { paddingBottom: insets.bottom + spacing.xl }]}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
        >
          <View style={styles.brand}>
            <Image source={require('../../../assets/logo.png')} style={styles.logo} resizeMode="contain" />
            <Text style={styles.brandName}>Green Light</Text>
            <Text style={styles.brandTagline}>Defensive Driving School</Text>
            <Text style={styles.brandSlogan}>Staff & Admin Portal</Text>
          </View>

          <View style={styles.formCard}>
            <Text style={styles.formTitle}>Staff login</Text>
            <Text style={styles.formSubtitle}>Sign in with your staff account</Text>

            {error ? <Text style={styles.error}>{error}</Text> : null}

            <FormInput
              label="Email"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
              placeholder="you@greenlight.co.ke"
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
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: colors.primary },
    container: { flexGrow: 1, justifyContent: 'center', padding: spacing.lg },
    brand: { alignItems: 'center', marginBottom: spacing.xl },
    logo: { width: 120, height: 120, marginBottom: spacing.md },
    brandName: { fontSize: 26, fontWeight: '800', color: colors.onPrimary },
    brandTagline: { fontSize: 14, color: colors.onPrimary, opacity: 0.9, marginTop: 2 },
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
  });
}
