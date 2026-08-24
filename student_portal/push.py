"""Send push notifications to student phones via the Expo push service."""
import logging

import requests

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send'


def send_push(student, title, body, data=None):
    """Best-effort push to a student's registered phone. Never raises."""
    token = (getattr(student, 'push_token', '') or '').strip()
    if not token:
        logger.info('No push token for student %s (%s)', student.pk, student.student_number)
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
            logger.warning('Expo push HTTP %s for student %s: %s', resp.status_code, student.pk, resp.text[:300])
        else:
            result = resp.json()
            tickets = result.get('data', [])
            for ticket in tickets:
                if ticket.get('status') == 'error':
                    logger.warning('Expo push ticket error for student %s: %s — %s',
                                   student.pk, ticket.get('message'), ticket.get('details'))
                    # Clear stale token so we stop retrying
                    err_msg = ticket.get('message', '')
                    if 'DeviceNotRegistered' in err_msg or 'InvalidCredentials' in err_msg:
                        student.push_token = ''
                        student.save(update_fields=['push_token'])
                        logger.info('Cleared stale push token for student %s', student.pk)
                else:
                    logger.info('Expo push sent to student %s: %s', student.pk, ticket.get('id'))
    except Exception as exc:
        logger.warning('Expo push error for student %s: %s', student.pk, exc)
