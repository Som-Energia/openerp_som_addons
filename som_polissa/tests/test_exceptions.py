# -*- coding: utf-8 -*-
import unittest


class IndexadaExceptionsTest(unittest.TestCase):
    def test_as_dict__IndexadaExceptionBase(self):
        e = indexada_exceptions.IndexadaException(  # noqa: F821
            "Title",
            "Description",
        )
        self.assertEqual(
            e.to_dict(),
            dict(
                code="IndexadaException",
                error="Description",
            ),
        )

    def test_as_dict__PolissaNotActive(self):
        e = indexada_exceptions.PolissaNotActive("0018")  # noqa: F821
        self.assertEqual(
            e.to_dict(),
            dict(
                code="PolissaNotActive",
                error=u"Pòlissa 0018 not active",
                polissa_number="0018",
            ),
        )

    def test_as_dict__PolissaModconPending(self):
        e = indexada_exceptions.PolissaModconPending("0018")  # noqa: F821
        self.assertEqual(
            e.to_dict(),
            dict(
                code="PolissaModconPending",
                error=u"Pòlissa 0018 already has a pending modcon",
                polissa_number="0018",
            ),
        )

    def test_as_dict__PolissaAlreadyIndexed(self):
        e = indexada_exceptions.PolissaAlreadyIndexed("0018")  # noqa: F821
        self.assertEqual(
            e.to_dict(),
            dict(
                code="PolissaAlreadyIndexed",
                error=u"Pòlissa 0018 already indexed",
                polissa_number="0018",
            ),
        )

    def test_as_dict__PolissaSimultaneousATR(self):
        e = indexada_exceptions.PolissaSimultaneousATR("0018")  # noqa: F821
        self.assertEqual(
            e.to_dict(),
            dict(
                code="PolissaSimultaneousATR",
                error=u"Pòlissa 0018 with simultaneous ATR",
                polissa_number="0018",
            ),
        )
