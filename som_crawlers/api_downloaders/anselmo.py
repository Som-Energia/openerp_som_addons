# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Anselmo(_config)


class Anselmo(Iberdrola):
    name = 'anselmo'
    cod_portal = '0118'
    process = None
