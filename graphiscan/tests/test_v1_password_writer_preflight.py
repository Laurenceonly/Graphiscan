"""Mock connections only; no private env/network imported."""
import unittest
from unittest.mock import MagicMock, Mock

from v1_backend import SupabasePostgresBackend
from tools.check_v1_password_writer import run_preflight

ENV = {'GRAPHISCAN_V1_PASSWORD_DATABASE_URL': 'synthetic-only'}


class WriterPreflightTests(unittest.TestCase):
    def setUp(self):
        self.backend = SupabasePostgresBackend(Mock(), Mock(), MagicMock())
        self.connect = self.backend.password_service.repository.connect
        self.cursor = self.connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        self.rows = [dict.fromkeys(('expected_role', 'read_only', 'utc', 'bounded', 'bounded_lock', 'restricted',
                                   'no_memberships', 'no_schema_create'), True),
                     dict.fromkeys(('operation_rls', 'no_direct_tables', 'no_sequences'), True),
                     dict.fromkeys(('definer', 'fixed_path', 'writer_allowed', 'clients_reader_denied', 'not_owner'), True),
                     dict.fromkeys(('definer', 'fixed_path', 'writer_allowed', 'clients_reader_denied', 'not_owner'), True)]
        self.cursor.fetchone.side_effect = self.rows
        self.factory = Mock(return_value=self.backend)

    def run_check(self, connect=True):
        return run_preflight(connect=connect, environ=ENV, backend_factory=self.factory)

    def test_offline_never_connects_and_missing_setting_never_builds_adapter(self):
        self.assertEqual(self.run_check(False)['status'], 'ready-to-connect')
        self.connect.assert_not_called()
        factory = Mock()
        self.assertEqual(run_preflight(environ={}, backend_factory=factory)['status'], 'blocked')
        factory.assert_not_called()

    def test_success_starts_read_only_and_only_executes_catalog_queries(self):
        report = self.run_check()
        self.assertEqual(report['status'], 'writer-preflight-passed')
        self.assertFalse(report['database_writes'])
        self.assertEqual(len(report['checks']), 23)
        calls = self.cursor.execute.call_args_list
        self.assertEqual(calls[0].args, ('SET TRANSACTION READ ONLY',))
        self.assertEqual(len(calls), 5)
        self.assertTrue(all(call.args[0].startswith('SELECT') for call in calls[1:]))
        self.assertEqual(calls[-1].args[1], ('public.graphiscan_complete_password(uuid,uuid,uuid)',))

    def test_any_bad_permission_flag_fails_closed(self):
        for index, key in ((0, 'restricted'), (0, 'no_memberships'), (1, 'no_direct_tables'),
                           (1, 'operation_rls'), (2, 'clients_reader_denied'), (3, 'fixed_path')):
            with self.subTest(key=key):
                rows = [dict(row) for row in self.rows]
                rows[index][key] = False
                self.cursor.fetchone.side_effect = rows
                self.assertEqual(self.run_check()['status'], 'failed')

    def test_database_failure_is_redacted(self):
        self.connect.side_effect = RuntimeError('private DSN password')
        report = self.run_check()
        self.assertEqual(report['status'], 'failed')
        self.assertNotIn('private', str(report))

    def test_missing_function_row_denied(self):
        self.cursor.fetchone.side_effect = self.rows[:2] + [None]
        self.assertEqual(self.run_check()['status'], 'failed')
