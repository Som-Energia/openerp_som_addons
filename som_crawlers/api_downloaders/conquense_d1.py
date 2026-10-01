# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config, **_kwargs):
    return Conquense_D1(_config)


class Conquense_D1(Conquense):
    name = 'conquense_d1'
    process = 'D1'
