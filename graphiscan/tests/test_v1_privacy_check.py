import unittest
from datetime import datetime,timezone
from unittest.mock import Mock,patch

from api_v1 import AccessState,ApiError,Identity,InvalidSession
from v1_backend import SupabasePostgresBackend
from tools import check_v1_privacy as checker

USER='00000000-0000-4000-8000-000000000001'
SESSION='00000000-0000-4000-8000-000000000002'


class PrivacyCheckerTests(unittest.TestCase):
    def setUp(self):
        self.backend=SupabasePostgresBackend(Mock(),Mock(),Mock(),Mock())
        self.backend.verifier.authenticate.return_value=Identity(USER,SESSION)
        self.provider=self.backend.password_service.provider
        self.accepted=self.revoked=False
        def access(identity):
            if self.revoked:raise InvalidSession()
            return AccessState(USER,'Synthetic Test Admin','admin','active',False,checker.VERSION,checker.VERSION if self.accepted else None)
        self.backend.repository.load_access.side_effect=access
        def call(method,path,**kwargs):
            if path=='/token?grant_type=password':return {'access_token':'synthetic'}
            if path=='/user':return {'id':USER,'email':checker.EMAIL}
            if path=='/logout?scope=local':self.revoked=True;return None
            raise AssertionError()
        self.provider.call.side_effect=call
        self.backend.privacy_service.get_agreement.return_value=dict(version=checker.VERSION,content=checker.NOTICE,title='Test',published_at='2026-10-20T00:00:00+00:00')
        def accept(identity,version,request):
            if version!=checker.VERSION:raise ApiError(409,'AGREEMENT_CHANGED','Changed')
            self.accepted=True
            return dict(agreement_version=version,accepted_at=datetime(2026,10,20,tzinfo=timezone.utc).isoformat())
        self.backend.privacy_service.accept.side_effect=accept

    def test_explicit_acceptance_verifies_round_trip_and_cleanup_without_printing_password(self):
        show=Mock()
        report=checker.run_check('fictional-private',self.backend,ask=lambda prompt:'ACCEPT TEST NOTICE',show=show)
        self.assertEqual(report['status'],'privacy-check-passed')
        self.assertTrue(self.revoked)
        show.assert_called_once_with(checker.NOTICE)
        self.assertNotIn('fictional-private',str(report))

    def test_decline_never_writes_acceptance_and_cleans_session(self):
        report=checker.run_check('fictional',self.backend,ask=lambda prompt:'no',show=Mock())
        self.assertEqual(report['status'],'declined')
        self.assertTrue(self.revoked)
        self.backend.privacy_service.accept.assert_not_called()

    def test_noncanonical_notice_is_not_displayed_or_accepted(self):
        self.backend.privacy_service.get_agreement.return_value['content']='Unreviewed text'
        ask,show=Mock(),Mock()
        self.assertEqual(checker.run_check('fictional',self.backend,ask=ask,show=show)['status'],'failed')
        ask.assert_not_called();show.assert_not_called()
        self.backend.privacy_service.accept.assert_not_called()

    def test_noninteractive_cli_refused(self):
        with patch.object(checker.sys,'argv',['check']),patch.object(checker.sys.stdin,'isatty',return_value=False),patch('builtins.print'):
            self.assertEqual(checker.main(),2)
