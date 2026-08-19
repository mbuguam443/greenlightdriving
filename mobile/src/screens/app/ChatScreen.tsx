import { Ionicons } from '@expo/vector-icons';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card, ErrorState, Loading } from '../../components/ui';
import { useTheme } from '../../context/ThemeContext';
import { api, getErrorMessage } from '../../services/apiClient';
import { colors, radius, shadows, spacing } from '../../theme/colors';
import { ChatMessage } from '../../types';

interface ChatBubbleProps {
  item: ChatMessage;
}

function ChatBubble({ item, colors }: ChatBubbleProps & { colors: any }) {
  const isMe = item.is_me;
  return (
    <View style={[styles.bubbleRow, isMe ? styles.bubbleRowEnd : styles.bubbleRowStart]}>
      <View style={[styles.bubble, isMe ? styles.bubbleMe : styles.bubbleOther]}>
        <View style={styles.bubbleHeader}>
          <View style={[styles.avatar, { backgroundColor: isMe ? colors.primaryDark : colors.primary }]}>
            <Text style={styles.avatarText}>{(item.user?.[0] ?? '?').toUpperCase()}</Text>
          </View>
          <Text style={[styles.senderName, { color: colors.primary }]} numberOfLines={1}>
            {item.user}
          </Text>
          {item.is_staff ? (
            <View style={[styles.staffBadge]}>
              <Text style={styles.staffBadgeText}>Staff</Text>
            </View>
          ) : null}
          <Text style={styles.timeText}>{item.date} {item.time}</Text>
        </View>
        <Text style={[styles.messageText, { color: colors.text }]}>{item.content}</Text>
      </View>
    </View>
  );
}

export default function ChatScreen() {
  const { colors } = useTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const flatListRef = useRef<FlatList>(null);
  const mountedRef = useRef(true);
  const lastCountRef = useRef(0);

  const fetchMessages = useCallback(async (silent = false) => {
    if (!silent) setRefreshing(true);
    try {
      const { data } = await api.get<{ messages: ChatMessage[] }>('/student/chat/');
      if (mountedRef.current) {
        const msgs = data.messages || [];
        if (msgs.length !== lastCountRef.current) {
          setMessages(msgs);
          lastCountRef.current = msgs.length;
        }
        setError('');
      }
    } catch (err) {
      if (mountedRef.current) setError(getErrorMessage(err));
    } finally {
      if (mountedRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    fetchMessages();
    return () => { mountedRef.current = false; };
  }, [fetchMessages]);

  useEffect(() => {
    const interval = setInterval(() => fetchMessages(true), 5000);
    return () => clearInterval(interval);
  }, [fetchMessages]);

  const sendMessage = useCallback(async () => {
    const content = text.trim();
    if (!content || sending) return;
    setSending(true);
    setText('');
    try {
      const { data: newMsg } = await api.post<ChatMessage>('/student/chat/', { content });
      setMessages((prev) => [...prev, newMsg]);
      lastCountRef.current = lastCountRef.current + 1;
    } catch (err) {
      setText(content);
      setError(getErrorMessage(err, 'Failed to send message.'));
    } finally {
      setSending(false);
    }
  }, [text, sending]);

  if (loading) return <Loading />;
  if (error && messages.length === 0) return <ErrorState message={error} onRetry={fetchMessages} />;

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]} edges={['top']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={0}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => <ChatBubble item={item} colors={colors} />}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => fetchMessages(true)} tintColor={colors.primary} />
          }
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="chatbubbles-outline" size={40} color={colors.textMuted} />
              <Text style={[styles.emptyText, { color: colors.textMuted }]}>No messages yet. Start the conversation!</Text>
            </View>
          }
        />
        {error && messages.length > 0 ? (
          <Text style={[styles.errorBanner, { color: colors.danger }]}>{error}</Text>
        ) : null}
        <View style={[styles.inputBar, { backgroundColor: colors.card, borderTopColor: colors.border }]}>
          <TextInput
            style={[styles.textInput, { color: colors.text, backgroundColor: colors.background, borderColor: colors.border }]}
            value={text}
            onChangeText={setText}
            placeholder="Type a message..."
            placeholderTextColor={colors.textMuted}
            maxLength={2000}
            multiline
          />
          <Pressable style={[styles.sendBtn, { backgroundColor: sending ? colors.primaryLight : colors.primary }]} onPress={sendMessage} disabled={sending}>
            <Ionicons name="send" size={20} color={colors.white} />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  flex: { flex: 1 },
  listContent: { padding: spacing.md, paddingBottom: spacing.sm },
  bubbleRow: { marginBottom: spacing.sm },
  bubbleRowEnd: { alignItems: 'flex-end' },
  bubbleRowStart: { alignItems: 'flex-start' },
  bubble: {
    maxWidth: '80%',
    borderRadius: 16,
    padding: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  bubbleMe: {
    backgroundColor: '#DCF8C6',
    borderBottomRightRadius: 4,
  },
  bubbleOther: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderBottomLeftRadius: 4,
  },
  bubbleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  avatar: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: colors.white,
    fontSize: 11,
    fontWeight: '700',
  },
  senderName: {
    fontSize: 12,
    fontWeight: '600',
  },
  staffBadge: {
    backgroundColor: `${colors.info}20`,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: radius.pill,
  },
  staffBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.info,
  },
  timeText: {
    fontSize: 10,
    color: colors.textMuted,
    marginLeft: 'auto',
  },
  messageText: {
    fontSize: 14,
    lineHeight: 20,
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: spacing.sm,
    padding: spacing.sm,
    borderTopWidth: 1,
  },
  textInput: {
    flex: 1,
    borderRadius: radius.lg,
    borderWidth: 1,
    paddingHorizontal: spacing.md,
    paddingVertical: 10,
    fontSize: 15,
    maxHeight: 100,
  },
  sendBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorBanner: {
    textAlign: 'center',
    fontSize: 12,
    paddingVertical: 4,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xl * 3,
  },
  emptyText: {
    fontSize: 14,
    marginTop: spacing.sm,
  },
});
