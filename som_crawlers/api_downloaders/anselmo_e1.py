# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config, **_kwargs):
    return Anselmo_E1(_config)


class Anselmo_E1(Anselmo):
    name = 'anselmo_e1'
    process = 'E1'
