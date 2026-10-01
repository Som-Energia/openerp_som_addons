# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config, **_kwargs):
    return Conquense_A3(_config)


class Conquense_A3(Conquense):
    name = 'conquense_a3'
    process = 'A3'
