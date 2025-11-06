# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Conquense(_config)


class Conquense(Iberdrola):
    name = 'conquense'
    cod_portal = '0032'
    process = None
