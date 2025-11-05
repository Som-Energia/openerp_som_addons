# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_M1(_config)


class Iberdrola_M1(Iberdrola):
    name = 'iberdrola_m1'
    process = 'M1'
