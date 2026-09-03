import Constants from 'expo-constants';

const configuredUrl = (Constants.expoConfig?.extra as { API_URL?: string } | undefined)?.API_URL;

function deriveDevHost(): string {
  try {
    const hostUri = Constants.expoConfig?.hostUri;
    if (hostUri) {
      const host = hostUri.split(':')[0];
      if (host) return host;
    }
  } catch {
    // fall through
  }
  return 'localhost';
}

export const API_URL = configuredUrl || `http://${deriveDevHost()}:8000/api`;
