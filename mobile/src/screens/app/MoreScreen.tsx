import { Ionicons } from '@expo/vector-icons';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { CompositeNavigationProp, useIsFocused, useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import React, { useEffect } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Card, ErrorState, Loading, SectionTitle } from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import { useTheme, ThemeMode } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { AppTabsParamList, MoreStackParamList } from '../../navigation/types';
import { colors, radius, shadows, spacing } from '../../theme/colors';
import { DashboardData } from '../../types';

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
  const { mode, setMode, isDark, colors: themeColors } = useTheme();
  const navigation = useNavigation<Nav>();
  const isFocused = useIsFocused();
  const { data, loading, error, refresh } = useApiData<DashboardData>('/student/dashboard/');

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  const goHomeScreen = (screen: 'Progress' | 'Documents' | 'Events' | 'Schedule' | 'Lessons') =>
    navigation.navigate('HomeTab', { screen });

  const menu: MenuRow[] = [
    { label: 'My Profile', icon: 'person-outline', color: themeColors.primary, onPress: () => navigation.navigate('Profile') },
    { label: 'My Lessons', icon: 'car-sport-outline', color: themeColors.info, onPress: () => goHomeScreen('Lessons') },
    { label: 'Schedule', icon: 'calendar-outline', color: themeColors.warning, onPress: () => goHomeScreen('Schedule') },
    { label: 'Progress & NTSA', icon: 'trending-up-outline', color: themeColors.success, onPress: () => goHomeScreen('Progress') },
    { label: 'Payments', icon: 'card-outline', color: '#8E24AA', onPress: () => navigation.navigate('PaymentsTab') },
    { label: 'Notifications', icon: 'notifications-outline', color: themeColors.danger, onPress: () => navigation.navigate('NotificationsTab') },
    { label: 'Events', icon: 'megaphone-outline', color: themeColors.red, onPress: () => goHomeScreen('Events') },
    { label: 'Documents', icon: 'documents-outline', color: '#0277BD', onPress: () => goHomeScreen('Documents') },
    { label: 'Chat', icon: 'chatbubbles-outline', color: '#00897B', onPress: () => navigation.navigate('Chat') },
  ];

  const logoutPress = () => {
    Alert.alert('Log out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log out', style: 'destructive', onPress: () => logout() },
    ]);
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: themeColors.background }]} edges={['top']}>
      {loading && !data ? (
        <Loading />
      ) : error && !data ? (
        <ErrorState message={error} onRetry={refresh} />
      ) : (
        <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
          <Pressable style={[styles.headerCard, { backgroundColor: themeColors.primary }]} onPress={() => navigation.navigate('Profile')}>
            <View style={[styles.avatar, { backgroundColor: themeColors.primaryDark }]}>
              <Text style={[styles.avatarText, { color: themeColors.white }]}>
                {`${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? ''}`.toUpperCase() || 'S'}
              </Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.name, { color: themeColors.white }]}>{user?.full_name || 'Student'}</Text>
              <Text style={[styles.email, { color: themeColors.white }]}>{user?.email}</Text>
              {data?.student ? (
                <View style={styles.badgeRow}>
                  <Badge text={data.student.student_number} />
                  <Badge text={data.student.status} color={themeColors.info} bg={`${themeColors.info}1A`} />
                </View>
              ) : null}
            </View>
            <Ionicons name="chevron-forward" size={20} color={themeColors.textMuted} />
          </Pressable>

          <SectionTitle title="Menu" />
          <Card style={[styles.menuCard, { backgroundColor: themeColors.card }]}>
            {menu.map((item, idx) => (
              <Pressable
                key={item.label}
                style={[styles.menuRow, idx < menu.length - 1 && [styles.menuRowBorder, { borderColor: themeColors.border }]]}
                onPress={item.onPress}
              >
                <View style={[styles.menuIcon, { backgroundColor: `${item.color}1A` }]}>
                  <Ionicons name={item.icon} size={20} color={item.color} />
                </View>
                <Text style={[styles.menuLabel, { color: themeColors.text }]}>{item.label}</Text>
                <Ionicons name="chevron-forward" size={18} color={themeColors.textMuted} />
              </Pressable>
            ))}
          </Card>

          <SectionTitle title="Appearance" />
          <Card style={[styles.menuCard, { backgroundColor: themeColors.card }]}>
            {(['light', 'dark', 'system'] as ThemeMode[]).map((opt, idx) => {
              const labels: Record<ThemeMode, string> = { light: 'Light Mode', dark: 'Dark Mode', system: 'System Default' };
              const icons: Record<ThemeMode, keyof typeof Ionicons.glyphMap> = {
                light: 'sunny-outline', dark: 'moon-outline', system: 'phone-portrait-outline'
              };
              return (
                <Pressable
                  key={opt}
                  style={[styles.menuRow, idx < 2 && [styles.menuRowBorder, { borderColor: themeColors.border }]]}
                  onPress={() => setMode(opt)}
                >
                  <View style={[styles.menuIcon, { backgroundColor: mode === opt ? `${themeColors.primary}20` : `${themeColors.textMuted}10` }]}>
                    <Ionicons name={icons[opt]} size={20} color={mode === opt ? themeColors.primary : themeColors.textMuted} />
                  </View>
                  <Text style={[styles.menuLabel, { color: mode === opt ? themeColors.primary : themeColors.text }, mode === opt && { fontWeight: '700' }]}>{labels[opt]}</Text>
                  {mode === opt ? <Ionicons name="checkmark-circle" size={20} color={themeColors.primary} /> : null}
                </Pressable>
              );
            })}
          </Card>

          <Pressable style={[styles.logoutBtn, { backgroundColor: `${themeColors.danger}14` }]} onPress={logoutPress}>
            <Ionicons name="log-out-outline" size={20} color={themeColors.danger} />
            <Text style={[styles.logoutText, { color: themeColors.danger }]}>Log out</Text>
          </Pressable>

          <Text style={[styles.version, { color: themeColors.textMuted }]}>Green Light Student App · v1.0.0</Text>
          <View style={styles.spacer} />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
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
    ...shadows.card,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: colors.white, fontSize: 20, fontWeight: '800' },
  name: { color: colors.white, fontSize: 17, fontWeight: '800' },
  email: { color: colors.white, opacity: 0.85, fontSize: 12, marginTop: 2 },
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
