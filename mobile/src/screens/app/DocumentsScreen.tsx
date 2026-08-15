import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect } from 'react';
import { Linking, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Badge, Card, EmptyState, ErrorState, Loading, SectionTitle } from '../../components/ui';
import { useApiData } from '../../hooks/useApiData';
import { API_URL } from '../../config/api';
import { colors, radius, spacing } from '../../theme/colors';
import { StudentDocument } from '../../types';
import { formatDate } from '../../utils/format';

const EXT_COLORS: Record<string, string> = {
  pdf: colors.danger,
  doc: colors.info,
  docx: colors.info,
  jpg: colors.warning,
  jpeg: colors.warning,
  png: colors.warning,
};

export default function DocumentsScreen() {
  const isFocused = useIsFocused();
  const { data, loading, error, refreshing, refresh } = useApiData<StudentDocument[]>('/student/documents/');

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  const openFile = async (doc: StudentDocument) => {
    if (!doc.file) return;
    const url = doc.file.startsWith('http') ? doc.file : `${API_URL.replace(/\/api$/, '')}${doc.file}`;
    const supported = await Linking.canOpenURL(url);
    if (supported) {
      Linking.openURL(url);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {loading ? (
        <Loading />
      ) : error && !data ? (
        <ErrorState message={error} onRetry={refresh} />
      ) : (
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.content}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}
        >
          <SectionTitle title="My documents" />
          {data && data.length === 0 ? (
            <EmptyState icon="documents-outline" title="No documents yet" subtitle="Documents shared by the school will appear here" />
          ) : (
            data?.map((doc) => {
              const ext = (doc.file_extension || '').toLowerCase();
              const color = EXT_COLORS[ext] || colors.primary;
              return (
                <Pressable key={doc.id} onPress={() => openFile(doc)} disabled={!doc.file}>
                  <Card style={styles.card}>
                    <View style={styles.row}>
                      <View style={[styles.iconWrap, { backgroundColor: `${color}1A` }]}>
                        <Ionicons name="document-text-outline" size={20} color={color} />
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.title}>{doc.title}</Text>
                        {doc.description ? <Text style={styles.desc}>{doc.description}</Text> : null}
                        <Text style={styles.meta}>
                          {doc.category} · {doc.file_size_display} · {formatDate(doc.uploaded_at)}
                        </Text>
                      </View>
                      {doc.file ? (
                        <View style={styles.download}>
                          <Ionicons name="download-outline" size={18} color={colors.primary} />
                          <Text style={styles.downloadText}>{ext.toUpperCase()}</Text>
                        </View>
                      ) : null}
                    </View>
                  </Card>
                </Pressable>
              );
            })
          )}
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
  card: { marginBottom: spacing.sm },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  iconWrap: {
    width: 42,
    height: 42,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: { fontSize: 14, fontWeight: '700', color: colors.text },
  desc: { fontSize: 12, color: colors.text, marginTop: 2 },
  meta: { fontSize: 11, color: colors.textMuted, marginTop: 4 },
  download: { alignItems: 'center', gap: 2 },
  downloadText: { fontSize: 10, fontWeight: '800', color: colors.primary },
  spacer: { height: spacing.lg },
});
