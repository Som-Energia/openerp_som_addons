# -*- coding: utf-8 -*-


class SomAccountInvoicePendingError(Exception):
    """Base class for other exceptions"""

    def __init__(self, msg):
        super(SomAccountInvoicePendingError, self).__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.__repr__()


class SMSException(SomAccountInvoicePendingError):
    """Raised when there is any error within SMS send"""

    def __init__(self, msg):
        super(SMSException, self).__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.__repr__()


class MailException(SomAccountInvoicePendingError):
    """Raised when there is any error within Email send"""

    def __init__(self, msg):
        super(MailException, self).__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.__repr__()


class UpdateWaitingFor48hException(SomAccountInvoicePendingError):
    def __init__(self, msg):
        super(SomAccountInvoicePendingError, self).__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.__repr__()


class UpdateWaitingForAnnexIVException(SomAccountInvoicePendingError):
    def __init__(self, msg):
        super(SomAccountInvoicePendingError, self).__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.__repr__()


class UpdateWaitingCancelledContractsException(SomAccountInvoicePendingError):
    def __init__(self, msg):
        super(SomAccountInvoicePendingError, self).__init__(msg)
        self.msg = msg

    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.__repr__()
