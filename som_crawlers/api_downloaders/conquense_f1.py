# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.conquense import Conquense
from som_crawlers.api_downloaders.iberdrola_f1 import Iberdrola_F1


def instance(_config, **_kwargs):
    return Conquense_F1(_config)


class Conquense_F1(Iberdrola_F1):
    name = 'conquense_f1'
    cod_portal = Conquense.cod_portal
    process = 'F1'
