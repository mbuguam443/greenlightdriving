import { Ionicons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import React, { useEffect, useState } from 'react';
import { FlatList, Image, Linking, Modal, Pressable, RefreshControl, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { WebView } from 'react-native-webview';
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

const IMAGE_EXTS = ['JPG', 'JPEG', 'PNG', 'GIF'];

function resolveFileUrl(file: string): string {
  return file.startsWith('http') ? file : `${API_URL.replace(/\/api$/, '')}${file}`;
}

export default function DocumentsScreen() {
  const isFocused = useIsFocused();
  const { width } = useWindowDimensions();
  const { data, loading, error, refreshing, refresh } = useApiData<StudentDocument[]>('/student/documents/');
  const [viewerIndex, setViewerIndex] = useState<number | null>(null);

  useEffect(() => {
    if (isFocused) refresh();
  }, [isFocused]);

  const openFile = async (doc: StudentDocument) => {
    if (!doc.file) return;
    const url = resolveFileUrl(doc.file);
    const ext = (doc.file_extension || '').toUpperCase();
    const index = data?.findIndex((item) => item.id === doc.id) ?? -1;
    if (index < 0) return;

    if (IMAGE_EXTS.includes(ext)) {
      setViewerIndex(index);
      return;
    }
    if (ext === 'PDF') {
      setViewerIndex(index);
      return;
    }
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
                      <View style={styles.details}>
                        <Text style={styles.title}>{doc.title}</Text>
                        {doc.description ? <Text style={styles.desc}>{doc.description}</Text> : null}
                        <Text style={styles.meta}>
                          {doc.category} · {doc.file_size_display} · {formatDate(doc.uploaded_at)}
                        </Text>
                      </View>
                      {doc.file ? (
                        <View style={styles.download}>
                          <Ionicons name="eye-outline" size={18} color={colors.primary} />
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

      <Modal visible={viewerIndex !== null} animationType="slide" onRequestClose={() => setViewerIndex(null)}>
        <SafeAreaView style={styles.viewerSafe} edges={['top', 'bottom']}>
          <View style={styles.viewerHeader}>
            <Text style={styles.viewerTitle} numberOfLines={1}>
              {viewerIndex !== null ? data?.[viewerIndex]?.title : ''}
            </Text>
            <Pressable onPress={() => setViewerIndex(null)} hitSlop={8} style={styles.viewerClose}>
              <Ionicons name="close" size={24} color={colors.text} />
            </Pressable>
          </View>
          <FlatList
            data={data ?? []}
            horizontal
            pagingEnabled
            initialScrollIndex={viewerIndex ?? 0}
            keyExtractor={(item) => String(item.id)}
            getItemLayout={(_, index) => ({ length: width, offset: width * index, index })}
            onMomentumScrollEnd={(event) => {
              const width = event.nativeEvent.layoutMeasurement.width;
              if (width) setViewerIndex(Math.round(event.nativeEvent.contentOffset.x / width));
            }}
            renderItem={({ item }) => {
              const url = item.file ? resolveFileUrl(item.file) : '';
              const ext = (item.file_extension || '').toUpperCase();
              return (
                <View style={[styles.viewerBody, { width }]}> 
                  {ext === 'PDF' ? (
                    <WebView source={{ uri: url }} style={styles.viewerWeb} originWhitelist={['*']} />
                  ) : IMAGE_EXTS.includes(ext) ? (
                    <Image source={{ uri: url }} style={styles.viewerImage} resizeMode="contain" />
                  ) : (
                    <Text style={styles.unsupported}>This document cannot be previewed here.</Text>
                  )}
                </View>
              );
            }}
          />
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  scroll: { flex: 1 },
  content: { padding: spacing.md },
  card: { marginBottom: spacing.sm },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  details: { flex: 1, minWidth: 0 },
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
  viewerSafe: { flex: 1, backgroundColor: colors.background },
  viewerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  viewerTitle: { flex: 1, fontSize: 15, fontWeight: '700', color: colors.text, marginRight: spacing.sm },
  viewerClose: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.border,
  },
  viewerBody: { flex: 1, backgroundColor: '#000' },
  viewerImage: { flex: 1, width: '100%' },
  viewerWeb: { flex: 1, backgroundColor: '#fff' },
  unsupported: { color: colors.white, textAlign: 'center', marginTop: spacing.xl },
});
