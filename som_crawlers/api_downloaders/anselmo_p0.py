# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config, **_kwargs):
    return Anselmo_P0(_config)


class Anselmo_P0(Anselmo):
    name = 'anselmo_p0'
    process = 'P0'
