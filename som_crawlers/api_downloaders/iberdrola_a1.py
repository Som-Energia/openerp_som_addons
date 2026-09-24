# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config, **_kwargs):
    return Iberdrola_A1(_config)


class Iberdrola_A1(Iberdrola):
    name = 'iberdrola_a1'
    process = 'A1'
