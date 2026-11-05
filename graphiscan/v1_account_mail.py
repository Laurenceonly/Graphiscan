"""Optional HTTPS credential delivery. No SMTP, credential storage or send retry."""
import re
from urllib.parse import urlsplit

import requests


def deliverable_address(value):
    if (not isinstance(value, str) or len(value) > 254
            or any(ord(c) < 33 or ord(c) == 127 for c in value)
            or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', value)):
        return False
    domain = value.rsplit('@', 1)[1].lower()
    return not domain.endswith('.') and not any(domain == suffix or domain.endswith('.' + suffix)
                   for suffix in ('invalid', 'test', 'example', 'localhost'))


class BrevoAccountMailer:
    def __init__(self, key, sender, access_url, *, admin_access_url='https://admin.graphiscan.site/login', http=None):
        parsed = urlsplit(access_url)
        if (not isinstance(key, str) or not key.strip() or '\n' in key or '\r' in key
                or not deliverable_address(sender) or parsed.scheme != 'https'
                or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment or any(c.isspace() for c in access_url)):
            raise ValueError('Configure the account email sender and public HTTPS access URL')
        self.key, self.sender, self.access_url = key, sender, access_url
        parsed = urlsplit(admin_access_url)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment or any(c.isspace() for c in admin_access_url)):
            raise ValueError('Configure a public HTTPS admin access URL')
        self.admin_access_url = admin_access_url
        self.http = http if http is not None else requests

    def send(self, fields, password):
        # Only called after confirmed profile completion. Never log request/response
        # bodies: both provider errors and the text contain private credentials.
        mobile = fields.get('role', 'teacher') in ('teacher', 'expert', 'parent')
        label = 'Temporary GraphiScan password' if mobile else 'GraphiScan password'
        access_url = self.access_url if mobile else self.admin_access_url
        instruction = ('On first sign-in, change the temporary password, then read and '
                       'accept the Data Privacy Agreement before using the features.' if mobile else
                       'Sign in with this password. You can change it in Settings.')
        text = ('Your GraphiScan account is ready.\n\n'
                f'Login ID: {fields["email"]}\n{label}: {password}\n\n'
                f'Open GraphiScan: {access_url}\n\n'
                'Use this password only for GraphiScan, not for your email inbox. '
                f'{instruction}\n\n'
                'If you were not expecting this account, contact the GraphiScan team. '
                'Do not forward these login details.')
        response = None
        try:
            response = self.http.request('POST', 'https://api.brevo.com/v3/smtp/email',
                headers={'api-key': self.key, 'Accept': 'application/json'},
                json={'sender': {'name': 'GraphiScan', 'email': self.sender},
                      'to': [{'email': fields['email']}],
                      'subject': 'Your GraphiScan account', 'textContent': text},
                timeout=(3.05, 8), allow_redirects=False)
            if response.status_code == 201:
                receipt = response.json()
                return 'accepted' if isinstance(receipt, dict) and isinstance(receipt.get('messageId'), str) and receipt['messageId'] else 'unknown'
            # Timeouts/server responses may have queued the email. Never retry.
            return 'failed' if 400 <= response.status_code < 500 and response.status_code != 408 else 'unknown'
        except (requests.RequestException, ValueError, TypeError):
            return 'unknown'
        finally:
            if response is not None:
                response.close()


def mailer_from_environment(env):
    values = [env.get(name, '') for name in ('GRAPHISCAN_ACCOUNT_MAIL_API_KEY',
              'GRAPHISCAN_ACCOUNT_MAIL_FROM', 'GRAPHISCAN_ACCOUNT_ACCESS_URL')]
    if not all(values):
        return None
    try:
        return BrevoAccountMailer(*values, admin_access_url=env.get('GRAPHISCAN_ACCOUNT_ADMIN_ACCESS_URL', 'https://admin.graphiscan.site/login'))
    except (ValueError, TypeError):
        return None
