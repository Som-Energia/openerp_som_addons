# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config, **_kwargs):
    return Conquense_Q1(_config)


class Conquense_Q1(Conquense):
    name = 'conquense_q1'
    process = 'Q1'
