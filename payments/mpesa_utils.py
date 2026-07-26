import base64
import datetime
import requests
from django.conf import settings


def get_access_token():
    """Get OAuth access token from Safaricom Daraja API."""
    url = f'{settings.MPESA_BASE_URL}/oauth/v1/generate'
    auth = f'{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}'
    encoded = base64.b64encode(auth.encode()).decode()
    headers = {'Authorization': f'Basic {encoded}'}

    try:
        resp = requests.get(url, headers=headers, params={'grant_type': 'client_credentials'}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get('access_token')
    except Exception as e:
        return None


def generate_password(timestamp):
    """Generate M-Pesa password using shortcode, passkey, and timestamp."""
    data_to_encode = f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'
    return base64.b64encode(data_to_encode.encode()).decode()


def format_phone(phone):
    """Format phone number to Safaricom format (254XXXXXXXXX)."""
    phone = phone.strip().replace(' ', '').replace('-', '').replace('+', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    if not phone.startswith('254'):
        phone = '254' + phone
    return phone


def initiate_stk_push(phone_number, amount, account_reference, transaction_desc):
    """
    Initiate M-Pesa STK Push (Lipa Na M-Pesa Online).
    Returns dict with success status, CheckoutRequestID, and message.
    """
    access_token = get_access_token()
    if not access_token:
        return {'success': False, 'message': 'Failed to get M-Pesa access token.'}

    url = f'{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest'
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = generate_password(timestamp)
    formatted_phone = format_phone(phone_number)

    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(float(amount)),
        'PartyA': formatted_phone,
        'PartyB': settings.MPESA_SHORTCODE,
        'PhoneNumber': formatted_phone,
        'CallBackURL': f'{settings.MPESA_CALLBACK_URL}/payments/mpesa/callback/',
        'AccountReference': str(account_reference)[:12],
        'TransactionDesc': str(transaction_desc)[:13],
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get('ResponseCode') == '0':
            return {
                'success': True,
                'checkout_request_id': data.get('CheckoutRequestID'),
                'merchant_request_id': data.get('MerchantRequestID'),
                'message': data.get('CustomerMessage', 'STK Push sent to your phone.'),
            }
        else:
            return {
                'success': False,
                'message': data.get('errorMessage', 'STK Push failed. Please try again.'),
            }
    except requests.exceptions.Timeout:
        return {'success': False, 'message': 'Request timed out. Please try again.'}
    except Exception as e:
        return {'success': False, 'message': f'Error: {str(e)}'}


def query_stk_push_status(checkout_request_id, merchant_request_id=''):
    """Query the status of an STK Push request."""
    access_token = get_access_token()
    if not access_token:
        return {'success': False, 'message': 'Failed to get access token.'}

    url = f'{settings.MPESA_BASE_URL}/mpesa/stkpushquery/v1/query'
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = generate_password(timestamp)

    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return {'success': True, 'data': resp.json()}
    except requests.exceptions.HTTPError as e:
        return {'success': False, 'message': f'HTTP {e.response.status_code}: {e.response.text}'}
    except Exception as e:
        return {'success': False, 'message': str(e)}
