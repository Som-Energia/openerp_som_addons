# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_R0(_config)


class Iberdrola_R0(Iberdrola):
    name = 'iberdrola_r0'
    process = 'R0'
