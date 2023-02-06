# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _

class LeadException(osv.except_osv):
    def __init__(self,  title, text, code=None, error_list=[]):
        super(LeadException, self).__init__(
            title,
            text
        )
        self.exc_type = 'error'
        self._code = code or self.__class__.__name__
        self._error_list = error_list

    @property
    def code(self):
        return self._code

    @property
    def error_list(self):
        return self._error_list

class InvalidParameters(LeadException):
    def __init__(self, invalid_fields=[]):
        super(InvalidParametersException, self).__init__(
            title=_('Invalid parameters'),
            text=_('Invalid parameters'),
            error_list=["Invalid {} value".format(field) for field in invalid_fields]
        )
        self.invalid_fields = invalid_fields

class InvalidLeadState(LeadException):
    def __init__(self, lead_id):
        error_text = _(u"El lead amb ID: {} no està en estat obert".format(lead_id))
        super(InvalidLeadState, self).__init__(
            title=_("Error"),
            text=error_text,
            error_list=[error_text],
        )

class MemberExists(LeadException):
    def __init__(self, partner_id):
        error_text = _(u"S'ha trobat un soci amb el partner_id {} i està actiu.").format(partner_id)
        super(MemberExists, self).__init__(
            title=_(u"Error al crear el soci"),
            text=error_test,
            error_list=[error_text],
        )

class ContributionInvoiceError(LeadException):
    def __init__(self, error_list=[]):
        super(ContributionInvoiceError, self).__init__(
            title=_(u"Error al crear la factura"),
            text= _(u"No s'han creat les factures."),
            error_list=error_list,
        )

class MissingMandatoryFields(LeadException):
    def __init__(self, missing_fields):
        error_text = _(u"Es deuen completar els següents camp '{0}'.").format(
            ', '.join(missing_fields)
        )
        super(MissingMandatoryFields, self).__init__(
            title=_(u"Falten Dades"),
            text=error_text,
            error_list=error_list,
        )

class PaymentOrderFailed(LeadException):
    def __init__(self, investment, invoice, errors):
        super(PaymentOrderFailed, self).__init__(
            title=_(u"Error al crear la orden de pagament"),
            text= _(u"No s'han crear la orden de pagament pel rebut {0} de l'aportació {1}.").format(invoice, investment),
            error_list=errors,
        )
        self.investment=investment
        self.invoice=invoice
