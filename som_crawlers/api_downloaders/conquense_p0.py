# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config, **_kwargs):
    return Conquense_P0(_config)


class Conquense_P0(Conquense):
    name = 'conquense_p0'
    process = 'P0'
