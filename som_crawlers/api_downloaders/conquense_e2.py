# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config, **_kwargs):
    return Conquense_E2(_config)


class Conquense_E2(Conquense):
    name = 'conquense_e2'
    process = 'E2'
