# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config, **_kwargs):
    return Anselmo_R1(_config)


class Anselmo_R1(Anselmo):
    name = 'anselmo_r1'
    process = 'R1'
