# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_P0(_config)


class Iberdrola_P0(Iberdrola):
    name = 'iberdrola_p0'
    process = 'P0'
