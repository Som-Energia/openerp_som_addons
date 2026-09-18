# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config, **_kwargs):
    return Conquense_C1(_config)


class Conquense_C1(Conquense):
    name = 'conquense_c1'
    process = 'C1'
