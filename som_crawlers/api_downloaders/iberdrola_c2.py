# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config, **_kwargs):
    return Iberdrola_C2(_config)


class Iberdrola_C2(Iberdrola):
    name = 'iberdrola_c2'
    process = 'C2'
