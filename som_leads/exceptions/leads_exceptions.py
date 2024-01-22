# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _

class LeadException(osv.except_osv):
    def __init__(self,  title, text):
        super(LeadException, self).__init__(
            title,
            text
        )
        # ERP error reporting as fatal error, not a discardable warning
        self.exc_type = 'error'
        self._message = text

    @property
    def code(self):
        return self.__class__.__name__

    def to_dict(self):
        return dict(
            code=self.code,
            error=self._message,
        )

class InvalidParameters(LeadException):
    def __init__(self, invalid_parameters=[]):
        super(InvalidParameters, self).__init__(
            title=_('Invalid parameters'),
            text=_("Invalid values for parameters {}").format(
            ', '.join(
                parameter for parameter in invalid_parameters
            )),
        )
        self.invalid_parameters = invalid_parameters

    def to_dict(self):
        return dict(
            super(InvalidParameters, self).to_dict(),
            invalid_parameters=self.invalid_parameters,
        )

class InvalidLeadState(LeadException):
    def __init__(self, lead_id):
        super(InvalidLeadState, self).__init__(
            title=_("Error"),
            text=_(u"El lead amb ID: {} no està en estat obert".format(lead_id)),
        )
        self._lead_id=lead_id

    def to_dict(self):
        return dict(
            super(InvalidLeadState, self).to_dict(),
            lead_id=self._lead_id,
        )

class MemberExists(LeadException):
    def __init__(self, partner_id):
        super(MemberExists, self).__init__(
            title=_(u"Error al crear el soci"),
            text=_(u"S'ha trobat un soci amb el partner_id {} i està actiu.").format(partner_id),
        )
        self.partner_id=partner_id

    def to_dict(self):
        return dict(
            super(MemberExists, self).to_dict(),
            partner_id=self.partner_id,
        )

class ContributionInvoiceError(LeadException):
    def __init__(self, error_list=[]):
        super(ContributionInvoiceError, self).__init__(
            title= _(u"No s'han creat les factures."),
            text= _(u"S'han produït els següents errors: {}").format(
            ', '.join(
                error for error in error_list
            )),
        )
        self.error_list = error_list

    def to_dict(self):
        return dict(
            super(ContributionInvoiceError, self).to_dict(),
            error_list=self.error_list,
        )

class MissingMandatoryFields(LeadException):
    def __init__(self, missing_fields):
        super(MissingMandatoryFields, self).__init__(
            title=_(u"Falten Dades"),
            text= _(u"Es deuen completar els següents camps '{0}'.").format(
            ', '.join(missing_fields)
            )
        )
        self.missing_fields = missing_fields

    def to_dict(self):
        return dict(
            super(MissingMandatoryFields, self).to_dict(),
            missing_fields=self.missing_fields,
        )

class PaymentOrderFailed(LeadException):
    def __init__(self, investment, invoice, errors):
        super(PaymentOrderFailed, self).__init__(
            title=_(u"Error al crear la orden de pagament"),
            text= _(u"No s'han crear la orden de pagament pel rebut {0} de l'aportació {1}.").format(invoice, investment),
        )
        self.investment=investment
        self.invoice=invoice
        self.error_list=errors

    def to_dict(self):
        return dict(
            super(PaymentOrderFailed, self).to_dict(),
            investment=self.investment,
            invoice=self.invoice,
            error_list=self.error_list,
        )