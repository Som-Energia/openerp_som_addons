# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config, **_kwargs):
    return Anselmo_B2(_config)


class Anselmo_B2(Anselmo):
    name = 'anselmo_b2'
    process = 'B2'
