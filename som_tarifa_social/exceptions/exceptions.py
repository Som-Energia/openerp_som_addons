# -*- coding: utf-8 -*-
from tools.translate import _

from addons.som_polissa.exceptions.exceptions import SomPolissaException


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
