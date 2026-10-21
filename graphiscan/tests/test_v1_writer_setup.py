"""Fictional URI tests only; no private configuration or network access."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from dotenv import dotenv_values
from tools import configure_v1_password_writer as setup

READER = 'postgresql://graphiscan_api_reader.fixture:synthetic@pool.example.invalid:5432/postgres?sslmode=verify-full&sslrootcert=C%3A%2Fsynthetic.crt'


class WriterSetupTests(unittest.TestCase):
    def test_preserves_pooler_tls_and_encodes_password_exactly_once(self):
        password = 'Synthetic@:/%?#+ quote\'\\2'
        uri = urlsplit(setup.writer_uri(READER, password))
        self.assertEqual(unquote(uri.username), 'graphiscan_password_writer.fixture')
        self.assertEqual(unquote(uri.password), password)
        self.assertEqual((uri.hostname, uri.port, uri.path, uri.query),
                         ('pool.example.invalid', 5432, '/postgres', urlsplit(READER).query))

    def test_refuses_missing_malformed_or_nonreader_uri(self):
        for value in ('', 'not a URI', READER.replace('graphiscan_api_reader', 'postgres'),
                      READER.replace('graphiscan_api_reader.fixture', 'graphiscan_api_reader_impostor'),
                      READER + '#fragment'):
            with self.assertRaises(ValueError):
                setup.writer_uri(value, 'fictional')
        with self.assertRaises(ValueError):
            setup.writer_uri(READER, '')

    def test_direct_reader_and_ipv6_supported(self):
        uri = setup.writer_uri('postgresql://graphiscan_api_reader:old@[::1]:5432/postgres', 'synthetic')
        self.assertEqual(urlsplit(uri).username, 'graphiscan_password_writer')
        self.assertEqual(urlsplit(uri).hostname, '::1')

    def test_hidden_prompt_writes_only_writer_and_does_not_echo_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / '.env'
            env.write_text('GRAPHISCAN_V1_DATABASE_URL=' + READER + '\nOTHER_SETTING=preserve\n', encoding='utf8')
            password = 'Synthetic-private@/%2'
            with patch.object(setup, 'ENV_PATH', env), patch.object(setup.sys, 'argv', ['setup']), \
                    patch.object(setup.sys.stdin, 'isatty', return_value=True), \
                    patch.object(setup.getpass, 'getpass', return_value=password), patch('builtins.print') as output:
                self.assertEqual(setup.main(), 0)
            values = dotenv_values(env, interpolate=False)
            self.assertEqual(values['GRAPHISCAN_V1_DATABASE_URL'], READER)
            self.assertEqual(values['OTHER_SETTING'], 'preserve')
            self.assertEqual(unquote(urlsplit(values['GRAPHISCAN_V1_PASSWORD_DATABASE_URL']).password), password)
            self.assertNotIn(password, str(output.call_args_list))
            self.assertNotIn(READER, str(output.call_args_list))

    def test_existing_writer_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / '.env'
            original = 'GRAPHISCAN_V1_PASSWORD_DATABASE_URL=synthetic-existing\n'
            env.write_text(original, encoding='utf8')
            with patch.object(setup, 'ENV_PATH', env), patch.object(setup.sys, 'argv', ['setup']), \
                    patch.object(setup.sys.stdin, 'isatty', return_value=True), \
                    patch.object(setup.getpass, 'getpass') as prompt, patch('builtins.print'):
                self.assertEqual(setup.main(), 2)
                prompt.assert_not_called()
            self.assertEqual(env.read_text(encoding='utf8'), original)

    def test_noninteractive_and_argument_input_refused(self):
        for argv, tty in [(['setup', 'private-password'], True), (['setup'], False)]:
            with patch.object(setup.sys, 'argv', argv), patch.object(setup.sys.stdin, 'isatty', return_value=tty), \
                    patch.object(setup.getpass, 'getpass') as prompt, patch('builtins.print'):
                self.assertEqual(setup.main(), 2)
                prompt.assert_not_called()
