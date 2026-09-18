# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config, **_kwargs):
    return Iberdrola_B2(_config)


class Iberdrola_B2(Iberdrola):
    name = 'iberdrola_b2'
    process = 'B2'
