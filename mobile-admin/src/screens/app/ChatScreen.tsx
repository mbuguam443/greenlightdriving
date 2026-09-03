import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '../../context/ThemeContext';
import { api } from '../../services/apiClient';
import { ChatMessage } from '../../types';
import { radius, spacing } from '../../theme/colors';

export default function ChatScreen() {
  const { colors } = useTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [text, setText] = useState('');
  const flatListRef = useRef<FlatList>(null);

  const loadMessages = async () => {
    try {
      const { data } = await api.get<ChatMessage[]>('/admin/chat/');
      setMessages(data);
    } catch {}
  };

  useEffect(() => {
    loadMessages();
    const interval = setInterval(loadMessages, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSend = async () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setText('');
    try {
      await api.post('/admin/chat/', { content: trimmed });
      await loadMessages();
    } catch {}
  };

  const grouped = useMemo(() => {
    const groups: { date: string; items: ChatMessage[] }[] = [];
    let current: ChatMessage[] = [];
    let currentDate = '';
    messages.forEach((m) => {
      if (m.date !== currentDate) {
        if (current.length > 0) groups.push({ date: currentDate, items: current });
        currentDate = m.date;
        current = [];
      }
      current.push(m);
    });
    if (current.length > 0) groups.push({ date: currentDate, items: current });
    return groups;
  }, [messages]);

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <FlatList
        ref={flatListRef}
        data={grouped}
        keyExtractor={(item) => item.date}
        contentContainerStyle={styles.list}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
        renderItem={({ item: group }) => (
          <View>
            <View style={styles.dateSeparator}>
              <Text style={[styles.dateText, { color: colors.textMuted }]}>{group.date}</Text>
            </View>
            {group.items.map((msg: ChatMessage) => {
              const isMe = msg.is_me;
              return (
                <View key={msg.id} style={[styles.bubbleRow, isMe && styles.bubbleRowMe]}>
                  <View style={[styles.bubble, { backgroundColor: isMe ? colors.chatMe : colors.chatOther }]}>
                    {!isMe && <Text style={[styles.sender, { color: colors.primary }]}>{msg.user}</Text>}
                    <Text style={[styles.bubbleText, { color: colors.text }]}>{msg.content}</Text>
                    <Text style={[styles.time, { color: colors.textMuted }]}>{msg.time}</Text>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      />
      <View style={[styles.inputBar, { backgroundColor: colors.card, borderTopColor: colors.border, paddingBottom: insets.bottom || spacing.sm }]}>
        <TextInput
          value={text}
          onChangeText={setText}
          placeholder="Type a message..."
          placeholderTextColor={colors.textMuted}
          style={[styles.input, { backgroundColor: colors.inputBg, color: colors.inputText }]}
          multiline
        />
        <View style={[styles.sendBtn, { backgroundColor: colors.primary }]}>
          <Ionicons name="send" size={20} color={colors.onPrimary} onPress={handleSend} />
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

function makeStyles(colors: ReturnType<typeof useTheme>['colors']) {
  return StyleSheet.create({
    container: { flex: 1 },
    list: { padding: spacing.md, paddingBottom: spacing.sm },
    dateSeparator: { alignItems: 'center', marginVertical: spacing.sm },
    dateText: { fontSize: 11, fontWeight: '600' },
    bubbleRow: { marginBottom: spacing.sm, alignItems: 'flex-start' },
    bubbleRowMe: { alignItems: 'flex-end' },
    bubble: { maxWidth: '80%', borderRadius: radius.lg, padding: spacing.sm },
    sender: { fontSize: 11, fontWeight: '700', marginBottom: 2 },
    bubbleText: { fontSize: 14, lineHeight: 20 },
    time: { fontSize: 10, marginTop: 4, alignSelf: 'flex-end' },
    inputBar: {
      flexDirection: 'row',
      alignItems: 'flex-end',
      paddingHorizontal: spacing.sm,
      paddingTop: spacing.sm,
      borderTopWidth: 1,
    },
    input: {
      flex: 1,
      borderRadius: radius.lg,
      paddingHorizontal: spacing.md,
      paddingVertical: 8,
      fontSize: 14,
      maxHeight: 100,
      marginRight: spacing.sm,
    },
    sendBtn: {
      width: 40,
      height: 40,
      borderRadius: 20,
      alignItems: 'center',
      justifyContent: 'center',
    },
  });
}
