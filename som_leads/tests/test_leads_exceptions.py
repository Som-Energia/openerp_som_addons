# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from destral import testing
import unittest
from ..exceptions.leads_exceptions import (
    LeadException,
    InvalidLeadState,
    InvalidParameters,
    MemberExists,
    ContributionInvoiceError,
    MissingMandatoryFields,
    PaymentOrderFailed,
)

class LeadExceptionsTest(unittest.TestCase):
    def test_as_dict__leadExceptionBase(self):
        e = LeadException(
            "Title",
            "Description",
        )
        self.assertEqual(e.to_dict(), dict(
            code="LeadException",
            error="Description",
        ))

    def test_as_dict__InvalidLeadState(self):
        e = InvalidLeadState(65)
        self.assertEqual(e.to_dict(), dict(
            code="InvalidLeadState",
            error=u"El lead amb ID: 65 no està en estat obert",
            lead_id=65,
        ))

    def test_as_dict__InvalidParameters__single_parameter(self):
        e = InvalidParameters(['myparam'])
        self.assertEqual(e.to_dict(), dict(
            code="InvalidParameters",
            error=u"Invalid values for parameters myparam",
            invalid_parameters=['myparam'],
        ))

    def test_as_dict__InvalidParameters__many_parameters(self):
        e = InvalidParameters(['myparam', 'otherparam'])
        self.assertEqual(e.to_dict(), dict(
            code="InvalidParameters",
            error=u"Invalid values for parameters myparam, otherparam",
            invalid_parameters=['myparam', 'otherparam'],
        ))
    
    def test_as_dict__MemeberExists(self):
        e = MemberExists(75)
        self.assertEqual(e.to_dict(), dict(
            code="MemberExists",
            error=u"S'ha trobat un soci amb el partner_id 75 i està actiu.",
            partner_id=75,
        ))

    def test_as_dict__ContributionInvoiceError_one_error(self):
        e = ContributionInvoiceError(['myerror'])
        self.assertEqual(e.to_dict(), dict(
            code="ContributionInvoiceError",
            error=u"S'han produït els següents errors: myerror",
            error_list=['myerror'],
        ))

    def test_as_dict__ContributionInvoiceError_many_errors(self):
        e = ContributionInvoiceError(['myerror', 'othererror'])
        self.assertEqual(e.to_dict(), dict(
            code="ContributionInvoiceError",
            error=u"S'han produït els següents errors: myerror, othererror",
            error_list=['myerror', 'othererror'],
        ))

    def test_as_dict__MissingMandatoryFields_one_field(self):
        e = MissingMandatoryFields(['myfield'])
        self.assertEqual(e.to_dict(), dict(
            code="MissingMandatoryFields",
            error=u"Es deuen completar els següents camps 'myfield'.",
            missing_fields=['myfield'],
        ))

    def test_as_dict__MissingMandatoryFields_many_fields(self):
        e = MissingMandatoryFields(['myfield', 'otherfield'])
        self.assertEqual(e.to_dict(), dict(
            code="MissingMandatoryFields",
            error=u"Es deuen completar els següents camps 'myfield, otherfield'.",
            missing_fields=['myfield', 'otherfield']
        ))

    def test_as_dict__PaymentOrderFailed(self):
        e = PaymentOrderFailed(10, 11, ['myerror'])
        self.assertEqual(e.to_dict(), dict(
            code="PaymentOrderFailed",
            error=u"No s'han crear la orden de pagament pel rebut 11 de l'aportació 10.",
            investment=10,
            invoice=11,
            error_list=['myerror'],
        ))