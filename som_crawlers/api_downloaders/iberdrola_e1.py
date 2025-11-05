# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_E1(_config)


class Iberdrola_E1(Iberdrola):
    name = 'iberdrola_e1'
    process = 'E1'
