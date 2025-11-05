# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config):
    return Iberdrola_F1(_config)


class Iberdrola_F1(Iberdrola):
    name = 'iberdrola_f1'
    process = 'F1'
