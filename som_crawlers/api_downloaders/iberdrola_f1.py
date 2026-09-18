# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config, **_kwargs):
    return Iberdrola_F1(_config)


class Iberdrola_F1(Iberdrola):
    name = 'iberdrola_f1'
    process = 'F1'
