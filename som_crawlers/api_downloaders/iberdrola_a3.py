# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_A3(_config)


class Iberdrola_A3(Iberdrola):
    name = 'iberdrola_a3'
    process = 'A3'
