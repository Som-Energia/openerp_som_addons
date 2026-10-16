# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config, **_kwargs):
    return Conquense_F1(_config)


class Conquense_F1(Conquense):
    name = 'conquense_f1'
    process = 'F1'
