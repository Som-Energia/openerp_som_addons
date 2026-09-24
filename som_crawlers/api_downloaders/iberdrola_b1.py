# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config, **_kwargs):
    return Iberdrola_B1(_config)


class Iberdrola_B1(Iberdrola):
    name = 'iberdrola_b1'
    process = 'B1'
