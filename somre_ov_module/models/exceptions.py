# -*- coding: utf-8 -*-

class SomreOvException(Exception):
    def __init__(self, text):
        self.exc_type = 'error'
        self.text = text
        super(SomreOvException, self).__init__(self.text)

    @property
    def code(self):
        return self.__class__.__name__

    def to_dict(self):
        return dict(
            code=self.code,
            error=self.text,
        )


class NoSuchUser(SomreOvException):
    def __init__(self):
        super(NoSuchUser, self).__init__(
            text="User does not exist"
        )


class NoDocumentVersions(SomreOvException):
    def __init__(self, document):
        super(NoDocumentVersions, self).__init__(
            text="Document {} has no version available to sign".format(document)
        )


class FailSendEmail(SomreOvException):
    def __init__(self, message):
        super(FailSendEmail, self).__init__(
            text=message or "Error sending email",
        )


class ContractWithoutInstallation(SomreOvException):
    def __init__(self, contract_number):
        super(ContractWithoutInstallation, self).__init__(
            text="No installation found for contract '{}'".format(contract_number))
        self.contract_number = contract_number

    def to_dict(self):
        return dict(
            super(ContractWithoutInstallation, self).to_dict(),
            contract_number=self.contract_number,
        )


class ContractNotExists(SomreOvException):
    def __init__(self):
        super(ContractNotExists, self).__init__(
            text="Contract does not exist")


class UnauthorizedAccess(SomreOvException):
    def __init__(self, username, resource_type, resource_name):
        super(UnauthorizedAccess, self).__init__(
            text="User {username} cannot access the {resource_type} '{resource_name}'".format(
                username=username,
                resource_type=resource_type,
                resource_name=resource_name,
            ))
        self.username = username
        self.resource_type = resource_type
        self.resource_name = resource_name

    def to_dict(self):
        return dict(
            super(UnauthorizedAccess, self).to_dict(),
            username=self.username,
            resource_type=self.resource_type,
            resource_name=self.resource_name,
        )


class NoSuchInvoice(SomreOvException):
    def __init__(self, invoice_number):
        super(NoSuchInvoice, self).__init__(
            text="No invoice found with number '{}'".format(invoice_number))
        self.invoice_number = invoice_number

    def to_dict(self):
        return dict(
            super(NoSuchInvoice, self).to_dict(),
            invoice_number=self.invoice_number,
        )
