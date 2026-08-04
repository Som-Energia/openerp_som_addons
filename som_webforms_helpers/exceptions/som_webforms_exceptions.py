# -*- coding: utf-8 -*-


class SomWebformsException(Exception):
    def __init__(self, text):
        self.exc_type = "error"
        self.text = text

    @property
    def code(self):
        return self.__class__.__name__

    def to_dict(self):
        return dict(
            code=self.code,
            error=self.text,
        )


class TariffNonExists(SomWebformsException):
    def __init__(self):
        super(TariffNonExists, self).__init__(text="Tariff pricelist not found")


class ContractWithoutModcons(SomWebformsException):
    def __init__(self):
        super(ContractWithoutModcons, self).__init__(text="Contract without modcontractual")


class InvalidModcons(SomWebformsException):
    def __init__(self):
        super(InvalidModcons, self).__init__(text="Contract with invalid modcons")


class InvalidSimulationPricelist(SomWebformsException):
    def __init__(self):
        super(InvalidSimulationPricelist, self).__init__(
            text="Simulation pricelist must be 'index' or 'periods'"
        )


class InvalidSimulationPowers(SomWebformsException):
    def __init__(self):
        super(InvalidSimulationPowers, self).__init__(
            text="Simulation powers must be between 1 and 100"
        )


class MissingSimulationConfig(SomWebformsException):
    def __init__(self):
        super(MissingSimulationConfig, self).__init__(
            text="Simulation configuration not found"
        )
