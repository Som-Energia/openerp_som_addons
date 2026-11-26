# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config, **_kwargs):
    return Iberdrola_P0(_config)


class Iberdrola_P0(Iberdrola):
    name = 'iberdrola_p0'
    process = 'P0'
