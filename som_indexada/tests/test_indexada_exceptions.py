# -*- coding: utf-8 -*-
from ..exceptions.indexada_exceptions import *
import unittest

class IndexadaExceptionsTest(unittest.TestCase):
    def test_as_dict__IndexadaExceptionBase(self):
        e = IndexadaException(
            "Title",
            "Description",
        )
        self.assertEqual(e.to_dict(), dict(
            code="IndexadaException",
            error="Description",
        ))

    def test_as_dict__PolissaNotActive(self):
        e = PolissaNotActive('0018')
        self.assertEqual(e.to_dict(), dict(
            code="PolissaNotActive",
            error=u"Pòlissa 0018 not active",
            polissa_number='0018',
        ))

    def test_as_dict__PolissaModconPending(self):
        e = PolissaModconPending('0018')
        self.assertEqual(e.to_dict(), dict(
            code="PolissaModconPending",
            error=u"Pòlissa 0018 already has a pending modcon",
            polissa_number='0018',
        ))

    def test_as_dict__PolissaAlreadyIndexed(self):
        e =  PolissaAlreadyIndexed('0018')
        self.assertEqual(e.to_dict(), dict(
            code="PolissaAlreadyIndexed",
            error=u"Pòlissa 0018 already indexed",
            polissa_number='0018',
        ))

    def test_as_dict__PolissaSimultaneousATR(self):
        e =  PolissaSimultaneousATR('0018')
        self.assertEqual(e.to_dict(), dict(
            code="PolissaSimultaneousATR",
            error=u"Pòlissa 0018 with simultaneous ATR",
            polissa_number='0018',
        ))
