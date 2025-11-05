# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_D1(_config)


class Iberdrola_D1(Iberdrola):
    name = 'iberdrola_d1'
    process = 'D1'
