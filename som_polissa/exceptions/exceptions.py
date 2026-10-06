# -*- coding: utf-8 -*-
import traceback
from osv import osv
from tools.translate import _


class SomPolissaException(osv.except_osv):
    def __init__(self, title, text, exception=None):
        super(SomPolissaException, self).__init__(
            title,
            text,
        )
        # ERP error reporting as fatal error, not a discardable warning
        if exception:
            message = '{} \n {}'.format(text, exception)
        else:
            message = text
        self.exc_type = 'error'
        self._message = message

    @property
    def code(self):
        return self.__class__.__name__

    def to_dict(self):
        return dict(
            code=self.code,
            error=self._message,
        )


class UnexpectedException(SomPolissaException):
    def __init__(self):
        super(UnexpectedException, self).__init__(
            title=_("Unexpected exception"),
            text=traceback.format_exc()
        )

    @property
    def code(self):
        return "Unexpected"


class PolissaModcontractual(SomPolissaException):
    def __init__(self, polissa_number):
        super(PolissaModcontractual, self).__init__(
            title=_("Pòlissa modcon"),
            text=_("Pòlissa {} in modcontractual state").format(polissa_number),
        )
        self.polissa_number = polissa_number

    def to_dict(self):
        return dict(
            super(PolissaModcontractual, self).to_dict(),
            polissa_number=self.polissa_number,
        )


class PolissaNotActive(SomPolissaException):
    def __init__(self, polissa_number, exception=None):
        super(PolissaNotActive, self).__init__(
            title=_("Pòlissa not active"),
            text=_("Pòlissa {} not active").format(polissa_number),
            exception=exception
        )
        self.polissa_number = polissa_number

    def to_dict(self):
        return dict(
            super(PolissaNotActive, self).to_dict(),
            polissa_number=self.polissa_number,
        )


class PolissaModconPending(SomPolissaException):
    def __init__(self, polissa_number, exception=None):
        super(PolissaModconPending, self).__init__(
            title=_("Pending modcon"),
            text=_("Pòlissa {} already has a pending modcon").format(polissa_number),
            exception=exception
        )
        self.polissa_number = polissa_number

    def to_dict(self):
        return dict(
            super(PolissaModconPending, self).to_dict(),
            polissa_number=self.polissa_number,
        )


class PolissaAlreadyIndexed(SomPolissaException):
    def __init__(self, polissa_number, exception=None):
        super(PolissaAlreadyIndexed, self).__init__(
            title=_("Already indexed"),
            text=_("Pòlissa {} already indexed").format(polissa_number),
            exception=exception
        )
        self.polissa_number = polissa_number

    def to_dict(self):
        return dict(
            super(PolissaAlreadyIndexed, self).to_dict(),
            polissa_number=self.polissa_number,
        )


class PolissaAlreadyPeriod(SomPolissaException):
    def __init__(self, polissa_number, exception=None):
        super(PolissaAlreadyPeriod, self).__init__(
            title=_("Already period"),
            text=_("Pòlissa {} already period").format(polissa_number),
            exception=exception
        )
        self.polissa_number = polissa_number

    def to_dict(self):
        return dict(
            super(PolissaAlreadyPeriod, self).to_dict(),
            polissa_number=self.polissa_number,
        )


class PolissaSimultaneousATR(SomPolissaException):
    def __init__(self, polissa_number, exception=None):
        super(PolissaSimultaneousATR, self).__init__(
            title=_("Simultaneous ATR"),
            text=_("Pòlissa {} with simultaneous ATR").format(polissa_number),
            exception=exception
        )
        self.polissa_number = polissa_number

    def to_dict(self):
        return dict(
            super(PolissaSimultaneousATR, self).to_dict(),
            polissa_number=self.polissa_number,
        )


class PolissaNotStandardPrice(SomPolissaException):
    def __init__(self, polissa_number, exception=None):
        super(PolissaNotStandardPrice, self).__init__(
            title=_("Non standard pricelist"),
            text=_("Pòlissa {} has a non-standard pricelist").format(polissa_number),
            exception=exception
        )
        self.polissa_number = polissa_number

    def to_dict(self):
        return dict(
            super(PolissaNotStandardPrice, self).to_dict(),
            polissa_number=self.polissa_number,
        )


class FailSendEmail(SomPolissaException):
    def __init__(self, polissa_number, exception=None):
        super(FailSendEmail, self).__init__(
            title=_("Email fail"),
            text=_("Failed to send email to Pòlissa {}").format(polissa_number),
            exception=exception
        )
        self.polissa_number = polissa_number

    def to_dict(self):
        return dict(
            super(FailSendEmail, self).to_dict(),
            polissa_number=self.polissa_number,
        )


class KCoefficientNotFound(SomPolissaException):
    def __init__(self, pricelist_id, exception=None):
        super(KCoefficientNotFound, self).__init__(
            title=_("K_Coefficient not found"),
            text=_("K_Coefficient not found for pricelist id {}").format(pricelist_id),
            exception=exception
        )
        self.pricelist_id = pricelist_id

    def to_dict(self):
        return dict(
            super(KCoefficientNotFound, self).to_dict(),
            pricelist_id=self.pricelist_id,
        )


class TariffCodeNotSupported(SomPolissaException):
    def __init__(self, tariff_code, exception=None):
        super(TariffCodeNotSupported, self).__init__(
            title=_("Tariff code not supported"),
            text=_("Change with tariff code {} not supported").format(tariff_code),
            exception=exception
        )
        self.tariff_code = tariff_code

    def to_dict(self):
        return dict(
            super(TariffCodeNotSupported, self).to_dict(),
            tariff_code=self.tariff_code,
        )


class TariffNonExists(SomPolissaException):
    def __init__(self, tariff, exception=None):
        super(TariffNonExists, self).__init__(
            title=_("Tariff not found"),
            text="Tariff {} not found".format(tariff),
            exception=exception
        )

    def to_dict(self):
        return dict(
            super(TariffNonExists, self).to_dict(),
        )


class InvalidSubsystem(SomPolissaException):
    def __init__(self, geo_zone, exception=None):
        super(InvalidSubsystem, self).__init__(
            title=_("Wrong geo zone"),
            text="Wrong geo zone {}".format(geo_zone),
            exception=exception
        )

    def to_dict(self):
        return dict(
            super(InvalidSubsystem, self).to_dict()
        )


class InvalidDates(SomPolissaException):
    def __init__(self, first_date, last_date, exception=None):
        super(InvalidDates, self).__init__(
            title="Invalid range dates",
            text="Invalid range dates [{} - {}]".format(first_date, last_date),
            exception=exception
        )

    def to_dict(self):
        return dict(
            super(InvalidDates, self).to_dict(),
        )


class PolissaCannotChangeSocialTariff(SomPolissaException):
    def __init__(self, polissa_number, change_type, exception=None):
        super(PolissaCannotChangeSocialTariff, self).__init__(
            title=_("Cannot change {} tariff").format(change_type),
            text=_("Pòlissa {} cannot change {} tariff").format(polissa_number, change_type),
            exception=exception
        )
        self.polissa_number = polissa_number
        self.change_type = change_type

    def to_dict(self):
        return dict(
            super(PolissaCannotChangeSocialTariff, self).to_dict(),
            polissa_number=self.polissa_number,
            change_type=self.change_type,
        )
