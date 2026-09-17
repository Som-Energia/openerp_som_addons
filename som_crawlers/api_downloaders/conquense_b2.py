# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config, **_kwargs):
    return Conquense_B2(_config)


class Conquense_B2(Conquense):
    name = 'conquense_b2'
    process = 'B2'
