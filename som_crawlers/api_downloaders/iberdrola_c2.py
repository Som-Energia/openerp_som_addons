# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_C2(_config)


class Iberdrola_C2(Iberdrola):
    name = 'iberdrola_c2'
