# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config, **_kwargs):
    return Anselmo_C2(_config)


class Anselmo_C2(Anselmo):
    name = 'anselmo_c2'
    process = 'C2'
