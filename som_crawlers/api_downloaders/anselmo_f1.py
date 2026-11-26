# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.anselmo import Anselmo
from som_crawlers.api_downloaders.iberdrola_f1 import Iberdrola_F1


def instance(_config, **_kwargs):
    return Anselmo_F1(_config)


class Anselmo_F1(Iberdrola_F1):
    name = 'anselmo_f1'
    cod_portal = Anselmo.cod_portal
    process = 'F1'
