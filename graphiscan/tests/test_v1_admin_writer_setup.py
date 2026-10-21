"""Read-only rollout orchestration checks; no private config or network."""
import unittest
from unittest.mock import MagicMock, Mock, patch

from tools import check_v1_admin_writer as setup
from v1_backend import SupabasePostgresBackend

CONNECTION = dict(read_only=True, utc=True, bounded=True, restricted=True)
CATALOG = dict.fromkeys(('restricted_role', 'no_role_memberships', 'bounded_schema_access',
    'no_direct_table_access', 'no_direct_sequence_access', 'guarded_update_function',
    'writer_can_update', 'other_runtime_roles_denied', 'public_denied',
    'other_application_functions_denied'), True)


class AdminWriterSetupTests(unittest.TestCase):
    def setUp(self):
        self.backend = Mock(spec=SupabasePostgresBackend)
        self.backend.admin_write_service = None
        self.reader = MagicMock()
        self.backend.repository = Mock()
        self.backend.repository.connect.return_value.__enter__ = Mock(return_value=self.reader)
        self.backend.repository.connect.return_value.__exit__ = Mock(return_value=False)
        self.cursor = self.reader.cursor.return_value.__enter__.return_value
        self.cursor.fetchone.side_effect = [CONNECTION, {'installed': True}, CATALOG]
        self.patch = patch.object(setup, 'backend_from_environment', return_value=self.backend)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_offline_default_never_connects(self):
        report = setup.run()
        self.assertEqual(report['status'], 'ready-to-connect')
        self.assertFalse(report['network_attempted'])
        self.backend.repository.connect.assert_not_called()

    def test_missing_migration_stops_before_writer_or_account_calls(self):
        self.cursor.fetchone.side_effect = [CONNECTION, {'installed': False}]
        report = setup.run(True)
        self.assertEqual(report['status'], 'migration-required')
        self.assertFalse(report['database_writes'])
        self.assertEqual(self.cursor.execute.call_count, 2)

    def test_catalog_failure_blocks_writer_and_errors_do_not_disclose_details(self):
        self.cursor.fetchone.side_effect = [CONNECTION, {'installed': True},
                                           dict(CATALOG, public_denied=False)]
        self.assertEqual(setup.run(True)['status'], 'blocked')
        self.cursor.execute.side_effect = RuntimeError('synthetic private connection text')
        report = setup.run(True)
        self.assertEqual(report['status'], 'failed')
        self.assertNotIn('private connection', str(report))

    def test_success_requires_writer_readonly_transaction_and_exact_role(self):
        self.assertEqual(setup.run(True)['status'], 'writer-configuration-required')
        self.cursor.fetchone.side_effect = [CONNECTION, {'installed': True}, CATALOG]
        writer = MagicMock()
        service = Mock()
        service.repository.connect.return_value.__enter__ = Mock(return_value=writer)
        service.repository.connect.return_value.__exit__ = Mock(return_value=False)
        self.backend.admin_write_service = service
        cursor = writer.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [CONNECTION, {'exact_role': True, 'lock_bounded': True}]
        report = setup.run(True)
        self.assertEqual(report['status'], 'admin-writer-setup-passed')
        self.assertEqual(cursor.execute.call_args_list[0].args, ('SET TRANSACTION READ ONLY',))
        self.assertFalse(report['database_writes'])
        for call in self.cursor.execute.call_args_list + cursor.execute.call_args_list:
            self.assertNotIn('SELECT public.graphiscan_update_account(', call.args[0])


if __name__ == '__main__':
    unittest.main()
