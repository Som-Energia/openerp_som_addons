# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_A1(_config)


class Iberdrola_A1(Iberdrola):
    name = 'iberdrola_a1'
    process = 'A1'
