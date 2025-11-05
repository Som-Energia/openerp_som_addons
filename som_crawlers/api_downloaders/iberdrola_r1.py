# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_R1(_config)


class Iberdrola_R1(Iberdrola):
    name = 'iberdrola_r1'
    process = 'R1'
