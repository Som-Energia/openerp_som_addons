# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config, **_kwargs):
    return Conquense_J1(_config)


class Conquense_J1(Conquense):
    name = 'conquense_j1'
    process = 'J1'
