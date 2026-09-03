import React, { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { Card, Button } from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { radius, spacing } from '../../theme/colors';

export default function ProfileScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { user, logout } = useAuth();

  return (
    <ScrollView style={{ backgroundColor: colors.background }} contentContainerStyle={styles.container}>
      <View style={[styles.avatar, { backgroundColor: colors.primary }]}>
        <Ionicons name="person" size={48} color={colors.onPrimary} />
      </View>
      <Text style={[styles.name, { color: colors.text }]}>{user?.full_name || 'Admin User'}</Text>
      <Text style={[styles.email, { color: colors.textMuted }]}>{user?.email}</Text>
      <Badge text={user?.role || 'ADMIN'} color={colors.primary} bg={`${colors.primary}1A`} />

      <Card style={styles.section}>
        <InfoRow icon="call-outline" label="Phone" value={user?.phone || 'N/A'} colors={colors} />
        <InfoRow icon="shield-checkmark-outline" label="Role" value={user?.role || 'ADMIN'} colors={colors} />
      </Card>

      <Card style={styles.section}>
        <InfoRow icon="school-outline" label="Green Light Admin" value="v1.0.0" colors={colors} />
      </Card>

      <Button title="Log Out" variant="danger" onPress={logout} icon="log-out-outline" style={styles.logoutBtn} />
    </ScrollView>
  );
}

function InfoRow({ icon, label, value, colors }: { icon: string; label: string; value: string; colors: any }) {
  return (
    <View style={infoStyles.row}>
      <View style={infoStyles.left}>
        <Ionicons name={icon as any} size={18} color={colors.textMuted} />
        <Text style={[infoStyles.label, { color: colors.textMuted }]}>{label}</Text>
      </View>
      <Text style={[infoStyles.value, { color: colors.text }]}>{value}</Text>
    </View>
  );
}

function Badge({ text, color, bg }: { text: string; color: string; bg: string }) {
  return (
    <View style={[badgeStyles.badge, { backgroundColor: bg }]}>
      <Text style={[badgeStyles.text, { color }]}>{text}</Text>
    </View>
  );
}

const badgeStyles = StyleSheet.create({
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999, alignSelf: 'center', marginTop: spacing.sm },
  text: { fontSize: 12, fontWeight: '700' },
});

const infoStyles = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10 },
  left: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  label: { fontSize: 14 },
  value: { fontSize: 14, fontWeight: '600' },
});

function makeStyles(colors: ReturnType<typeof useTheme>['colors']) {
  return StyleSheet.create({
    container: { alignItems: 'center', padding: spacing.lg, paddingBottom: spacing.xl * 2 },
    avatar: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md },
    name: { fontSize: 20, fontWeight: '800' },
    email: { fontSize: 13, marginTop: 2 },
    section: { width: '100%', marginTop: spacing.md },
    logoutBtn: { width: '100%', marginTop: spacing.xl },
  });
}
