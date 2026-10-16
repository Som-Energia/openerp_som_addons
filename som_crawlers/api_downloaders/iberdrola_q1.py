# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config, **_kwargs):
    return Iberdrola_Q1(_config)


class Iberdrola_Q1(Iberdrola):
    name = 'iberdrola_q1'
    process = 'Q1'
