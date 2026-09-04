import * as DocumentPicker from 'expo-document-picker';
import React, { useMemo, useState } from 'react';
import {
  Alert,
  FlatList,
  Linking,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Card, EmptyState, Loading, ErrorState, Badge, Button, FormInput } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { useApiData } from '../../hooks/useApiData';
import { api, getErrorMessage } from '../../services/apiClient';
import { DocumentRecord, StudentRecord } from '../../types';
import { radius, spacing } from '../../theme/colors';

const CATEGORIES = [
  { value: 'general', label: 'General' },
  { value: 'theory', label: 'Theory Materials' },
  { value: 'forms', label: 'Forms' },
  { value: 'certificates', label: 'Certificates' },
  { value: 'guidelines', label: 'Guidelines' },
  { value: 'ntsa', label: 'NTSA Documents' },
];

function Chip({
  label,
  active,
  onPress,
  colors,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
  colors: any;
}) {
  const styles = makeStyles(colors);
  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.chip,
        { borderColor: active ? colors.primary : colors.border, backgroundColor: active ? `${colors.primary}1A` : colors.card },
      ]}
    >
      <Text style={[styles.chipText, { color: active ? colors.primary : colors.text }]}>{label}</Text>
    </Pressable>
  );
}

export default function DocumentsScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { data, loading, error, refreshing, refresh } = useApiData<DocumentRecord[]>('/admin/documents/');
  const { data: students } = useApiData<StudentRecord[]>('/admin/students/', []);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('general');
  const [studentId, setStudentId] = useState<number | null>(null);
  const [picked, setPicked] = useState<{ name: string; uri: string; mimeType?: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handlePick = async () => {
    try {
      const res = await DocumentPicker.getDocumentAsync({
        type: '*/*',
        copyToCacheDirectory: true,
        multiple: false,
      });
      if (!res.canceled && res.assets && res.assets.length > 0) {
        const a = res.assets[0];
        setPicked({ name: a.name, uri: a.uri, mimeType: a.mimeType });
      }
    } catch (err) {
      Alert.alert('Error', getErrorMessage(err, 'Could not pick a file.'));
    }
  };

  const handleUpload = async () => {
    if (!title.trim()) {
      Alert.alert('Error', 'Please enter a document title.');
      return;
    }
    if (!picked) {
      Alert.alert('Error', 'Please choose a file to upload.');
      return;
    }
    const form = new FormData();
    form.append('title', title.trim());
    form.append('description', description.trim());
    form.append('category', category);
    if (studentId) form.append('student', String(studentId));
    form.append('file', {
      uri: picked.uri,
      name: picked.name,
      type: picked.mimeType || 'application/octet-stream',
    } as unknown as Blob);

    setSubmitting(true);
    try {
      await api.post('/admin/documents/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      Alert.alert('Uploaded', 'Document uploaded successfully.');
      setTitle('');
      setDescription('');
      setCategory('general');
      setStudentId(null);
      setPicked(null);
      setShowForm(false);
      refresh();
    } catch (err) {
      Alert.alert('Error', getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Button
        title={showForm ? 'Cancel' : 'Upload Document'}
        variant={showForm ? 'outline' : 'primary'}
        onPress={() => setShowForm(!showForm)}
        icon={showForm ? 'close-outline' : 'cloud-upload-outline'}
        style={styles.uploadBtn}
      />

      {showForm && (
        <Card style={styles.formCard}>
          <FormInput label="Title" value={title} onChangeText={setTitle} placeholder="Document title" />
          <FormInput label="Description" value={description} onChangeText={setDescription} placeholder="Short description (optional)" multiline numberOfLines={2} style={{ height: 60, textAlignVertical: 'top' }} />

          <Text style={[styles.fieldLabel, { color: colors.text }]}>Category</Text>
          <View style={styles.chipWrap}>
            {CATEGORIES.map((c) => (
              <Chip key={c.value} label={c.label} active={category === c.value} onPress={() => setCategory(c.value)} colors={colors} />
            ))}
          </View>

          <Text style={[styles.fieldLabel, { color: colors.text }]}>
            Private document (optional) <Text style={{ fontStyle: 'italic' }}>- leave off for everyone</Text>
          </Text>
          <View style={styles.chipWrap}>
            <Chip label="Everyone" active={!studentId} onPress={() => setStudentId(null)} colors={colors} />
          </View>
          <View style={styles.chipWrap}>
            {(students || []).map((s) => (
              <Chip
                key={s.id}
                label={`${s.full_name} · ${s.student_number}`}
                active={studentId === s.id}
                onPress={() => setStudentId(s.id)}
                colors={colors}
              />
            ))}
            {!students || students.length === 0 ? (
              <Text style={[styles.hint, { color: colors.textMuted }]}>No students available.</Text>
            ) : null}
          </View>

          <Button title={picked ? `File: ${picked.name}` : 'Choose File'} variant="outline" onPress={handlePick} icon="attach-outline" style={styles.pickBtn} />
          <Button title="Upload" onPress={handleUpload} loading={submitting} icon="cloud-upload-outline" />
        </Card>
      )}

      <FlatList
        data={data || []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={!data || data.length === 0 ? styles.emptyContainer : styles.list}
        ListEmptyComponent={showForm ? null : <EmptyState icon="documents-outline" title="No documents yet" />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <View style={styles.header}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.title, { color: colors.text }]}>{item.title}</Text>
                <Text style={[styles.sub, { color: colors.textMuted }]}>{item.category_display} · {item.file_size_display}</Text>
              </View>
              <Badge text={item.file_extension} color={colors.info} />
            </View>
            {item.description ? (
              <Text style={[styles.desc, { color: colors.textMuted }]}>{item.description}</Text>
            ) : null}
            {item.target_student_name ? (
              <Text style={[styles.privateTag, { color: colors.warning }]}>Private · {item.target_student_name}</Text>
            ) : null}
            <View style={styles.actions}>
              <Button title="Open" variant="outline" onPress={() => Linking.openURL(item.file)} icon="open-outline" style={styles.actionBtn} />
              <Button
                title="Delete"
                variant="danger"
                onPress={() => {
                  Alert.alert('Delete document', `Delete "${item.title}"?`, [
                    { text: 'Cancel', style: 'cancel' },
                    {
                      text: 'Delete',
                      style: 'destructive',
                      onPress: async () => {
                        try {
                          await api.delete(`/admin/documents/${item.id}/`);
                          refresh();
                        } catch (err) {
                          Alert.alert('Error', getErrorMessage(err));
                        }
                      },
                    },
                  ]);
                }}
                icon="trash-outline"
                style={styles.actionBtn}
              />
            </View>
          </Card>
        )}
      />
    </View>
  );
}

function makeStyles(colors: ReturnType<typeof useTheme>['colors']) {
  return StyleSheet.create({
    container: { flex: 1 },
    uploadBtn: { margin: spacing.md },
    formCard: { marginHorizontal: spacing.md, marginBottom: spacing.md },
    fieldLabel: { fontSize: 13, fontWeight: '600', marginTop: spacing.sm, marginBottom: 6 },
    chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.sm },
    chip: { paddingHorizontal: spacing.md, paddingVertical: 8, borderRadius: radius.pill, borderWidth: 1.5 },
    chipText: { fontSize: 12, fontWeight: '600' },
    hint: { fontSize: 12, fontStyle: 'italic' },
    pickBtn: { marginBottom: spacing.md },
    list: { paddingHorizontal: spacing.md, paddingBottom: spacing.xl },
    emptyContainer: { flex: 1 },
    card: { marginBottom: spacing.sm },
    header: { flexDirection: 'row', alignItems: 'flex-start' },
    title: { fontSize: 15, fontWeight: '700' },
    sub: { fontSize: 12, marginTop: 2 },
    desc: { fontSize: 12, marginTop: spacing.sm },
    privateTag: { fontSize: 11, marginTop: spacing.sm, fontWeight: '600' },
    actions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
    actionBtn: { flex: 1, height: 40 },
  });
}
