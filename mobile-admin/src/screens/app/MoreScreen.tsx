import { Ionicons } from '@expo/vector-icons';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { CompositeNavigationProp, useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import React, { useMemo } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Card, SectionTitle } from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import { ThemeColors, ThemeMode, useTheme } from '../../context/ThemeContext';
import { AppTabsParamList, HomeStackParamList, MoreStackParamList } from '../../navigation/types';
import { radius, spacing } from '../../theme/colors';

type Nav = CompositeNavigationProp<
  NativeStackNavigationProp<MoreStackParamList, 'More'>,
  BottomTabNavigationProp<AppTabsParamList>
>;

type MenuRow = {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  onPress: () => void;
};

export default function MoreScreen() {
  const { user, logout } = useAuth();
  const { mode, setMode, colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const navigation = useNavigation<Nav>();

  const menu: MenuRow[] = [
    { label: 'Send Notification', icon: 'notifications-outline', color: colors.danger, onPress: () => navigation.navigate('Notifications') },
    { label: 'Notification History', icon: 'time-outline', color: colors.info, onPress: () => navigation.navigate('Notifications') },
    { label: 'Admissions', icon: 'mail-outline', color: colors.warning, onPress: () => navigation.navigate('HomeTab', { screen: 'Admissions' }) },
    { label: 'School Chat', icon: 'chatbubbles-outline', color: '#00897B', onPress: () => navigation.navigate('Chat') },
    { label: 'Students', icon: 'people-outline', color: colors.primary, onPress: () => navigation.navigate('StudentsTab') },
    { label: 'Payments', icon: 'card-outline', color: '#8E24AA', onPress: () => navigation.navigate('PaymentsTab') },
  ];

  const logoutPress = () => {
    Alert.alert('Log out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log out', style: 'destructive', onPress: () => logout() },
    ]);
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        <Pressable style={styles.headerCard} onPress={() => navigation.navigate('Profile')}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {`${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? ''}`.toUpperCase() || 'A'}
            </Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{user?.full_name || 'Staff'}</Text>
            <Text style={styles.email}>{user?.email}</Text>
            <View style={styles.badgeRow}>
              <Badge text={user?.role ?? 'STAFF'} />
            </View>
          </View>
          <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
        </Pressable>

        <SectionTitle title="Menu" />
        <Card style={styles.menuCard}>
          {menu.map((item, idx) => (
            <Pressable
              key={item.label}
              style={[styles.menuRow, idx < menu.length - 1 && styles.menuRowBorder]}
              onPress={item.onPress}
            >
              <View style={[styles.menuIcon, { backgroundColor: `${item.color}1A` }]}>
                <Ionicons name={item.icon} size={20} color={item.color} />
              </View>
              <Text style={styles.menuLabel}>{item.label}</Text>
              <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
            </Pressable>
          ))}
        </Card>

        <SectionTitle title="Appearance" />
        <Card style={styles.menuCard}>
          {(['light', 'dark', 'system'] as ThemeMode[]).map((opt, idx, arr) => {
            const labels: Record<ThemeMode, string> = { light: 'Light Mode', dark: 'Dark Mode', system: 'System Default' };
            const icons: Record<ThemeMode, keyof typeof Ionicons.glyphMap> = {
              light: 'sunny-outline', dark: 'moon-outline', system: 'phone-portrait-outline'
            };
            return (
              <Pressable
                key={opt}
                style={[styles.menuRow, idx < arr.length - 1 && styles.menuRowBorder]}
                onPress={() => setMode(opt)}
              >
                <View style={[styles.menuIcon, { backgroundColor: mode === opt ? `${colors.primary}20` : `${colors.textMuted}10` }]}>
                  <Ionicons name={icons[opt]} size={20} color={mode === opt ? colors.primary : colors.textMuted} />
                </View>
                <Text style={[styles.menuLabel, mode === opt && { color: colors.primary, fontWeight: '700' }]}>{labels[opt]}</Text>
                {mode === opt ? <Ionicons name="checkmark-circle" size={20} color={colors.primary} /> : null}
              </Pressable>
            );
          })}
        </Card>

        <Pressable style={styles.logoutBtn} onPress={logoutPress}>
          <Ionicons name="log-out-outline" size={20} color={colors.danger} />
          <Text style={styles.logoutText}>Log out</Text>
        </Pressable>

        <Text style={styles.version}>Green Light Admin App · v1.0.0</Text>
        <View style={styles.spacer} />
      </ScrollView>
    </SafeAreaView>
  );
}

function makeStyles(colors: ThemeColors) {
  return StyleSheet.create({
    safe: { flex: 1, backgroundColor: colors.background },
    scroll: { flex: 1 },
    content: { padding: spacing.md },
    headerCard: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.md,
      backgroundColor: colors.primary,
      borderRadius: radius.lg,
      padding: spacing.lg,
      marginBottom: spacing.sm,
    },
    avatar: {
      width: 56,
      height: 56,
      borderRadius: 28,
      backgroundColor: colors.primaryDark,
      alignItems: 'center',
      justifyContent: 'center',
    },
    avatarText: { color: colors.onPrimary, fontSize: 20, fontWeight: '800' },
    name: { color: colors.onPrimary, fontSize: 17, fontWeight: '800' },
    email: { color: colors.onPrimary, opacity: 0.85, fontSize: 12, marginTop: 2 },
    badgeRow: { flexDirection: 'row', gap: 6, marginTop: spacing.sm },
    menuCard: { padding: 0, overflow: 'hidden' },
    menuRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.md,
      padding: spacing.md,
    },
    menuRowBorder: { borderBottomWidth: 1, borderBottomColor: colors.border },
    menuIcon: {
      width: 38,
      height: 38,
      borderRadius: 11,
      alignItems: 'center',
      justifyContent: 'center',
    },
    menuLabel: { flex: 1, fontSize: 15, fontWeight: '600', color: colors.text },
    logoutBtn: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: spacing.sm,
      backgroundColor: `${colors.danger}14`,
      borderRadius: radius.md,
      padding: spacing.md,
      marginTop: spacing.lg,
    },
    logoutText: { color: colors.danger, fontSize: 15, fontWeight: '700' },
    version: { textAlign: 'center', color: colors.textMuted, fontSize: 12, marginTop: spacing.lg },
    spacer: { height: spacing.lg },
  });
}
