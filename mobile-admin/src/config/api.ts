import Constants from 'expo-constants';

// Override in app.json -> expo.extra.API_URL for release builds, e.g.
//   "extra": { "API_URL": "https://greenlight-driving-defensive.schones-heim-builders.co.ke/api" }
const configuredUrl = (Constants.expoConfig?.extra as { API_URL?: string } | undefined)?.API_URL;

// In development, derive the host from the Metro bundler so the app can reach
// the Django server running on the same machine as the dev tools.
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
