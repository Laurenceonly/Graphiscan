"""Fictional credential delivery; no email, provider or database connection."""
import unittest
from unittest.mock import Mock

import requests

from api_v1 import ApiError, Identity
from v1_account_issuance import AccountIssuanceService
from v1_account_mail import BrevoAccountMailer, deliverable_address, mailer_from_environment

ACTOR = '00000000-0000-4000-8000-000000000001'
SESSION = '00000000-0000-4000-8000-000000000002'
TARGET = '00000000-0000-4000-8000-000000000003'
KEY = '00000000-0000-4000-8000-000000000004'
REQUEST = '00000000-0000-4000-8000-000000000005'


class AccountDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.repo, self.provider, self.mail = Mock(), Mock(), Mock()
        self.receipt = {'user_id': TARGET, 'must_change_password': True}
        self.repo.execute.side_effect = [
            {'result': {'code': None, 'reserved': True}},
            {'result': {'code': None, 'data': self.receipt}}]
        self.provider.create.return_value = TARGET
        self.mail.send.return_value = 'accepted'
        self.service = AccountIssuanceService(self.repo, self.provider, self.mail)
        self.body = dict(full_name='Fictional Teacher', email='fictional@example.com',
                         role='teacher', school_ids=['1'], temporary_password='Fictional!42Value', delivery_method='email')

    def create(self, **changes):
        return self.service.create(Identity(ACTOR, SESSION), {**self.body, **changes}, KEY, REQUEST)

    def test_delivery_follows_confirmed_completion_and_never_persists_credentials(self):
        events = []
        results = list(self.repo.execute.side_effect)
        self.repo.execute.side_effect = lambda *args: events.append('db') or results.pop(0)
        self.provider.create.side_effect = lambda *args: events.append('auth') or TARGET
        self.mail.send.side_effect = lambda *args: events.append('mail') or 'accepted'
        result = self.create()
        self.assertEqual(events, ['db', 'auth', 'db', 'mail'])
        self.assertEqual(result['credential_delivery'], {'method': 'email', 'status': 'accepted'})
        self.assertNotIn(self.body['temporary_password'], str(result))
        self.assertNotIn(self.body['temporary_password'], str(self.repo.execute.call_args_list))
        self.assertNotIn('delivery_method', str(self.repo.execute.call_args_list))

    def test_unconfigured_email_fails_before_issuance_but_manual_still_works(self):
        self.service.mailer = None
        with self.assertRaises(ApiError) as error:
            self.create()
        self.assertEqual(error.exception.code, 'ACCOUNT_EMAIL_UNAVAILABLE')
        self.repo.execute.assert_not_called()
        self.provider.create.assert_not_called()
        self.assertEqual(self.create(delivery_method='manual')['credential_delivery']['status'], 'manual')

    def test_manual_generated_login_never_sends_email(self):
        result = self.create(delivery_method='manual', email='gs-fictional@accounts.graphiscan.invalid')
        self.assertEqual(result['data'], self.receipt)
        self.mail.send.assert_not_called()

    def test_replay_never_sends_supplied_password_or_marks_it_current(self):
        self.repo.execute.side_effect = None
        self.repo.execute.return_value = {'result': {'code': None, 'data': self.receipt}}
        result = self.create(temporary_password='Different!42Value')
        self.assertEqual(result['credential_delivery']['status'], 'not_repeated')
        self.mail.send.assert_not_called()
        self.provider.create.assert_not_called()

    def test_email_failure_cannot_change_successful_account_receipt(self):
        self.mail.send.side_effect = RuntimeError('private provider/password details')
        result = self.create()
        self.assertEqual(result['data'], self.receipt)
        self.assertEqual(result['credential_delivery']['status'], 'unknown')
        self.assertNotIn('private', str(result))
        self.mail.send.assert_called_once()
        self.assertEqual(self.repo.execute.call_count, 2)

    def test_uncertain_profile_never_sends_mail(self):
        self.repo.execute.side_effect = [{'result': {'code': None, 'reserved': True}}, RuntimeError('private database details')]
        with self.assertRaises(ApiError) as error:
            self.create()
        self.assertEqual(error.exception.code, 'ACCOUNT_CREATION_PENDING')
        self.mail.send.assert_not_called()

    def test_invalid_mode_and_reserved_recipient_are_rejected_before_writes(self):
        for changes in ({'delivery_method': []}, {'delivery_method': 'sms'},
                        {'email': 'fictional@example.invalid'}, {'email': 'x@localhost.test'},
                        {'email': 'fictional@example.com\r\nBcc:x@example.com'}):
            with self.subTest(changes=changes), self.assertRaises(ApiError):
                self.create(**changes)
        self.repo.execute.assert_not_called()


class MailTransportTests(unittest.TestCase):
    def setUp(self):
        self.response = Mock(status_code=201)
        self.response.json.return_value = {'messageId': 'fictional-message'}
        self.http = Mock()
        self.http.request.return_value = self.response
        self.mail = BrevoAccountMailer('fictional-key', 'sender@example.com',
                                     'https://graphiscan.vercel.app/download/', http=self.http)
        self.fields = {'email': 'fictional@example.com'}

    def test_one_https_send_has_no_redirects_or_tokens_in_access_link(self):
        self.assertEqual(self.mail.send(self.fields, 'Fictional!42Value'), 'accepted')
        args, kwargs = self.http.request.call_args
        self.assertEqual(args, ('POST', 'https://api.brevo.com/v3/smtp/email'))
        self.assertFalse(kwargs['allow_redirects'])
        self.assertEqual(kwargs['json']['to'], [{'email': self.fields['email']}])
        self.assertIn('https://graphiscan.vercel.app/download/', kwargs['json']['textContent'])
        self.assertIn('change the temporary password', kwargs['json']['textContent'])
        self.response.close.assert_called_once()

    def test_rejections_and_uncertain_outcomes_never_retry_or_parse_error_text(self):
        for code, expected in ((400, 'failed'), (401, 'failed'), (429, 'failed'),
                               (408, 'unknown'), (500, 'unknown'), (302, 'unknown')):
            with self.subTest(code=code):
                self.http.request.reset_mock()
                self.response.json.reset_mock()
                self.response.status_code = code
                self.assertEqual(self.mail.send(self.fields, 'Fictional!42Value'), expected)
                self.http.request.assert_called_once()
                self.response.json.assert_not_called()
        self.http.request.side_effect = requests.Timeout('private password/provider details')
        self.assertEqual(self.mail.send(self.fields, 'Fictional!42Value'), 'unknown')

    def test_admin_and_researcher_receive_permanent_password_and_portal_link(self):
        for role in ('admin', 'researcher'):
            self.assertEqual(self.mail.send({**self.fields, 'role': role}, 'Fictional!42Value'), 'accepted')
            content = self.http.request.call_args.kwargs['json']['textContent']
            self.assertIn('GraphiScan password:', content)
            self.assertIn('https://admin.graphiscan.site/login', content)
            self.assertNotIn('temporary password', content)
            self.assertNotIn('/download/', content)

    def test_malformed_success_is_not_claimed_as_delivery(self):
        self.response.json.return_value = {}
        self.assertEqual(self.mail.send(self.fields, 'Fictional!42Value'), 'unknown')

    def test_configuration_requires_verified_style_address_and_clean_https_url(self):
        env = {'GRAPHISCAN_ACCOUNT_MAIL_API_KEY': 'fictional-key',
               'GRAPHISCAN_ACCOUNT_MAIL_FROM': 'sender@example.com',
               'GRAPHISCAN_ACCOUNT_ACCESS_URL': 'https://graphiscan.vercel.app/download/'}
        self.assertIsInstance(mailer_from_environment(env), BrevoAccountMailer)
        for key in env:
            self.assertIsNone(mailer_from_environment({**env, key: ''}))
        for url in ('http://example.com/', 'https://user:password@example.com/',
                    'https://example.com/?password=secret', 'https://example.com/#token',
                    'https://example.com/a\nb'):
            self.assertIsNone(mailer_from_environment({**env, 'GRAPHISCAN_ACCOUNT_ACCESS_URL': url}))
        self.assertFalse(deliverable_address('issued@accounts.graphiscan.invalid'))
        self.assertFalse(deliverable_address('issued@accounts.graphiscan.invalid.'))
        self.assertFalse(deliverable_address('bad\x00@example.com'))


if __name__ == '__main__':
    unittest.main()
