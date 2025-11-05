# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_B1(_config)


class Iberdrola_B1(Iberdrola):
    name = 'iberdrola_b1'
    process = 'B1'
