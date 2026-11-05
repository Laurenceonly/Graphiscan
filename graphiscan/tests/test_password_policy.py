"""Exercise legacy password helpers without importing credentials or live services."""
import ast
from pathlib import Path
import re
import unittest

from werkzeug.security import check_password_hash, generate_password_hash


class LegacyPasswordPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ast.parse((Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf-8'))
        names = {'validate_password_strength', 'pepper_password', 'hash_password', 'verify_password'}
        module = ast.Module(body=[node for node in source.body
                                  if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])
        cls.helpers = {'re': re, 'PASSWORD_PEPPER': 'fictional-test-only-pepper',
                       'generate_password_hash': generate_password_hash,
                       'check_password_hash': check_password_hash}
        exec(compile(module, '<legacy password helpers>', 'exec'), cls.helpers)

    def test_each_required_class_and_whitespace_only_symbol(self):
        validate = self.helpers['validate_password_strength']
        for value in ('abcdef1!', 'ABCDEF1!', 'Abcdefg!', 'Abcdefg1', 'Ab1!xyz',
                      'Abc def1', 'Abcdef1\t', 'Abcdef1\u00a0'):
            with self.subTest(case=value):
                self.assertTrue(validate(value))
        self.assertEqual(validate('Abcdef1!'), [])

    def test_hashes_are_salted_and_verify_only_the_correct_password(self):
        password = 'Fictional-only-1!'
        first, second = [self.helpers['hash_password'](password) for _ in range(2)]
        self.assertNotEqual(first, second)
        self.assertNotIn(password, first)
        self.assertEqual(self.helpers['verify_password'](first, password), (True, False))
        self.assertEqual(self.helpers['verify_password'](first, 'Wrong-only-2!'), (False, False))

    def test_existing_unpeppered_hash_is_marked_for_upgrade(self):
        password = 'Fictional-only-1!'
        old = generate_password_hash(password)
        self.assertEqual(self.helpers['verify_password'](old, password), (True, True))
