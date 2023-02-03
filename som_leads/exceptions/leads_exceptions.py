# -*- coding: utf-8 -*-
from osv import osv

class LeadException(osv.except_osv):
    def __init__(self,  title, text, code=None, error_list=[]):
        super(LeadException, self).__init__(
            title,
            text
        )
        self.exc_type = 'error'
        self._code = code
        self._error_list = error_list

    @property
    def code(self):
        return self._code

    @property
    def error_list(self):
        return self._error_list

class InvalidParametersException(LeadException):
    def __init__(self, title, text, error_list=[]):
        super(InvalidParametersException, self).__init__(
            title,
            text,
            '400',
            error_list
        )

class InvalidLeadState(LeadException):
    def __init__(self, title, text, error_list=[]):
        super(InvalidLeadState, self).__init__(
            title,
            text,
            '500',
            error_list
        )

class MemberExistsException(LeadException):
    def __init__(self, title, text, error_list=[]):
        super(MemberExistsException, self).__init__(
            title,
            text,
            '500',
            error_list
        )

class InvestmentException(LeadException):
    def __init__(self, title, text, error_list=[]):
        super(InvestmentException, self).__init__(
            title,
            text,
            '500',
            error_list
        )

class MandatoryFieldsException(LeadException):
    def __init__(self, title, text, error_list=[]):
        super(MandatoryFieldsException, self).__init__(
            title,
            text,
            '500',
            error_list
        )