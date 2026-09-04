import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import React, { useMemo } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { MoreStackParamList } from '../../navigation/types';
import { radius, spacing } from '../../theme/colors';

type Nav = NativeStackNavigationProp<MoreStackParamList>;

const MENU: { key: keyof MoreStackParamList; title: string; icon: keyof typeof Ionicons.glyphMap; desc: string }[] = [
  { key: 'Payments', title: 'Payments', icon: 'card-outline', desc: 'View records & record a payment' },
  { key: 'Lessons', title: 'Lessons', icon: 'book-outline', desc: 'Approve, mark lessons complete & attendance' },
  { key: 'Documents', title: 'Documents', icon: 'documents-outline', desc: 'Upload & manage learning materials' },
  { key: 'Enquiries', title: 'Enquiries', icon: 'call-outline', desc: 'Follow up & call enquiries' },
  { key: 'Notifications', title: 'Notifications', icon: 'notifications-outline', desc: 'Send notifications to students' },
  { key: 'Chat', title: 'Chat', icon: 'chatbubbles-outline', desc: 'Message students & staff' },
  { key: 'Profile', title: 'Profile', icon: 'person-circle-outline', desc: 'Your account settings' },
];

export default function MoreScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const navigation = useNavigation<Nav>();

  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={styles.container}
    >
      {MENU.map((m) => (
        <Pressable key={m.key} onPress={() => navigation.navigate(m.key)}>
          <Card style={styles.row}>
            <View style={[styles.iconWrap, { backgroundColor: `${colors.primary}1A` }]}>
              <Ionicons name={m.icon} size={20} color={colors.primary} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.title, { color: colors.text }]}>{m.title}</Text>
              <Text style={[styles.desc, { color: colors.textMuted }]}>{m.desc}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
          </Card>
        </Pressable>
      ))}
    </ScrollView>
  );
}

function makeStyles(colors: ReturnType<typeof useTheme>['colors']) {
  return StyleSheet.create({
    container: { padding: spacing.md, paddingBottom: spacing.xl * 2 },
    row: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm },
    iconWrap: {
      width: 42,
      height: 42,
      borderRadius: radius.md,
      alignItems: 'center',
      justifyContent: 'center',
      marginRight: spacing.md,
    },
    title: { fontSize: 15, fontWeight: '700' },
    desc: { fontSize: 12, marginTop: 2 },
  });
}
