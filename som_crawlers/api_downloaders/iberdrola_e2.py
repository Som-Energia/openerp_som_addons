# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_E2(_config)


class Iberdrola_E2(Iberdrola):
    name = 'iberdrola_e2'
    process = 'E2'
