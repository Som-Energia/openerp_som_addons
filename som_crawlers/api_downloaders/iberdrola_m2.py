# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_M2(_config)


class Iberdrola_M2(Iberdrola):
    name = 'iberdrola_m2'
    process = 'M2'
