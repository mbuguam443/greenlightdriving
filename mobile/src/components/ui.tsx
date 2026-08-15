import React from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleProp,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
  ViewStyle,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colors, radius, shadows, spacing } from '../theme/colors';

// ---------- Card ----------

export function Card({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return <View style={[styles.card, style]}>{children}</View>;
}

// ---------- Section title ----------

export function SectionTitle({ title, right }: { title: string; right?: React.ReactNode }) {
  return (
    <View style={styles.sectionTitleRow}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {right}
    </View>
  );
}

// ---------- Button ----------

type ButtonProps = {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'outline' | 'danger' | 'ghost';
  loading?: boolean;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
  icon?: keyof typeof Ionicons.glyphMap;
};

export function Button({
  title,
  onPress,
  variant = 'primary',
  loading = false,
  disabled = false,
  style,
  icon,
}: ButtonProps) {
  const isOutline = variant === 'outline';
  const isDanger = variant === 'danger';
  const isGhost = variant === 'ghost';
  const bg = isOutline || isGhost ? 'transparent' : isDanger ? colors.red : colors.primary;
  const border = isOutline ? colors.primary : isDanger ? colors.red : 'transparent';
  const fg = isOutline ? colors.primary : isGhost ? colors.primary : colors.white;

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: bg, borderColor: border },
        pressed && styles.buttonPressed,
        disabled && styles.buttonDisabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={isOutline ? colors.primary : colors.white} />
      ) : (
        <View style={styles.buttonContent}>
          {icon ? <Ionicons name={icon} size={18} color={fg} style={styles.buttonIcon} /> : null}
          <Text style={[styles.buttonText, { color: fg }]}>{title}</Text>
        </View>
      )}
    </Pressable>
  );
}

// ---------- Form input ----------

type FormInputProps = TextInputProps & {
  label?: string;
  error?: string;
};

export function FormInput({ label, error, style, ...props }: FormInputProps) {
  return (
    <View style={styles.inputGroup}>
      {label ? <Text style={styles.inputLabel}>{label}</Text> : null}
      <TextInput
        placeholderTextColor={colors.textMuted}
        style={[styles.input, error ? styles.inputError : null, style]}
        {...props}
      />
      {error ? <Text style={styles.inputErrorText}>{error}</Text> : null}
    </View>
  );
}

// ---------- Badge ----------

export function Badge({
  text,
  color = colors.primary,
  bg,
}: {
  text: string;
  color?: string;
  bg?: string;
}) {
  return (
    <View style={[styles.badge, { backgroundColor: bg ?? `${color}1A` }]}>
      <Text style={[styles.badgeText, { color }]}>{text}</Text>
    </View>
  );
}

// ---------- Stat card ----------

export function StatCard({
  label,
  value,
  icon,
  color = colors.primary,
}: {
  label: string;
  value: string;
  icon: keyof typeof Ionicons.glyphMap;
  color?: string;
}) {
  return (
    <Card style={styles.statCard}>
      <View style={[styles.statIcon, { backgroundColor: `${color}1A` }]}>
        <Ionicons name={icon} size={20} color={color} />
      </View>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </Card>
  );
}

// ---------- Progress bar ----------

export function ProgressBar({ value, color = colors.primary }: { value: number; color?: string }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <View style={styles.progressTrack}>
      <View style={[styles.progressFill, { backgroundColor: color, width: `${pct}%` }]} />
    </View>
  );
}

// ---------- Empty state ----------

export function EmptyState({
  icon = 'file-tray-outline',
  title = 'Nothing here yet',
  subtitle,
}: {
  icon?: keyof typeof Ionicons.glyphMap;
  title?: string;
  subtitle?: string;
}) {
  return (
    <View style={styles.emptyState}>
      <Ionicons name={icon} size={40} color={colors.textMuted} />
      <Text style={styles.emptyTitle}>{title}</Text>
      {subtitle ? <Text style={styles.emptySubtitle}>{subtitle}</Text> : null}
    </View>
  );
}

// ---------- Loading ----------

export function Loading() {
  return (
    <View style={styles.loading}>
      <ActivityIndicator size="large" color={colors.primary} />
    </View>
  );
}

// ---------- Error ----------

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <View style={styles.emptyState}>
      <Ionicons name="cloud-offline-outline" size={40} color={colors.danger} />
      <Text style={styles.emptyTitle}>Something went wrong</Text>
      <Text style={styles.emptySubtitle}>{message}</Text>
      {onRetry ? <Button title="Retry" onPress={onRetry} variant="outline" style={styles.retryBtn} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    padding: spacing.md,
    ...shadows.card,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
    marginTop: spacing.sm,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
  },
  button: {
    height: 48,
    borderRadius: radius.md,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.md,
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonIcon: {
    marginRight: 6,
  },
  buttonText: {
    fontSize: 15,
    fontWeight: '600',
  },
  buttonPressed: {
    opacity: 0.85,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  inputGroup: {
    marginBottom: spacing.md,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 6,
  },
  input: {
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 12,
    fontSize: 15,
    color: colors.text,
  },
  inputError: {
    borderColor: colors.danger,
  },
  inputErrorText: {
    color: colors.danger,
    fontSize: 12,
    marginTop: 4,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radius.pill,
    alignSelf: 'flex-start',
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  statCard: {
    alignItems: 'center',
    paddingVertical: spacing.md,
    flex: 1,
  },
  statIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.text,
  },
  statLabel: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
    textAlign: 'center',
  },
  progressTrack: {
    height: 8,
    borderRadius: radius.pill,
    backgroundColor: colors.border,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: radius.pill,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xl * 2,
    paddingHorizontal: spacing.lg,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text,
    marginTop: spacing.sm,
  },
  emptySubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 4,
    textAlign: 'center',
  },
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  retryBtn: {
    marginTop: spacing.md,
    paddingHorizontal: spacing.xl,
  },
});
