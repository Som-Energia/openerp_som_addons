# -*- coding: utf-8 -*-
from __future__ import absolute_import

import ast
import os

from addons import get_module_path
from destral import testing
from som_polissa.exceptions import exceptions
from tools import ustr


class TestSocialTariffException(testing.OOTestCaseWithCursor):

    def test_exception_has_one_definition_in_shared_module(self):
        owners = []
        for module in ('som_polissa', 'som_tarifa_social'):
            path = os.path.join(
                get_module_path(module), 'exceptions', 'exceptions.py',
            )
            if not os.path.isfile(path):
                continue
            with open(path, 'rb') as source:
                tree = ast.parse(source.read())
            for node in ast.walk(tree):
                if (isinstance(node, ast.ClassDef)
                        and node.name == 'PolissaCannotChangeSocialTariff'):
                    owners.append(module)

        self.assertEqual(owners, ['som_polissa'])

    def test_shared_exception_preserves_public_payload(self):
        error = exceptions.PolissaCannotChangeSocialTariff(
            'TEST-CONTRACT', 'to_social',
        )
        payload = error.to_dict()
        payload['error'] = ustr(payload['error'])

        self.assertIsInstance(error, exceptions.SomPolissaException)
        self.assertEqual(error.name, 'Cannot change to_social tariff')
        self.assertEqual(error.exc_type, 'error')
        self.assertEqual(payload, {
            'code': 'PolissaCannotChangeSocialTariff',
            'error': u'Pòlissa TEST-CONTRACT cannot change to_social tariff',
            'polissa_number': 'TEST-CONTRACT',
            'change_type': 'to_social',
        })

    def test_shared_exception_preserves_underlying_error_details(self):
        error = exceptions.PolissaCannotChangeSocialTariff(
            'TEST-CONTRACT', 'to_regular', exception=ValueError('Price missing'),
        )

        self.assertEqual(ustr(error.to_dict()['error']),
                         u'Pòlissa TEST-CONTRACT cannot change to_regular '
                         u'tariff \n Price missing')
        self.assertEqual(error.to_dict()['change_type'], 'to_regular')
