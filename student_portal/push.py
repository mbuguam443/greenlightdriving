"""Send push notifications to student phones via the Expo push service."""
import logging

import requests

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send'


def send_push(student, title, body, data=None):
    """Best-effort push to a student's registered phone. Never raises."""
    token = (getattr(student, 'push_token', '') or '').strip()
    if not token:
        return
    payload = {
        'to': token,
        'title': title[:200],
        'body': body[:1000],
        'sound': 'default',
        'priority': 'high',
        'channelId': 'messages',
    }
    if data:
        payload['data'] = data
    try:
        resp = requests.post(EXPO_PUSH_URL, json=payload, timeout=10)
        if resp.status_code >= 400:
            logger.warning('Expo push failed (%s): %s', resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning('Expo push error: %s', exc)
