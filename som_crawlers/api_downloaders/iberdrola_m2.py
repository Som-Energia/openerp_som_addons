# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config, **_kwargs):
    return Iberdrola_M2(_config)


class Iberdrola_M2(Iberdrola):
    name = 'iberdrola_m2'
    process = 'M2'
