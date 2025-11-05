# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_J1(_config)


class Iberdrola_J1(Iberdrola):
    name = 'iberdrola_j1'
    process = 'J1'
