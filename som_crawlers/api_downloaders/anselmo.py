# -*- coding: utf-8 -*-
from __future__ import absolute_import
from som_crawlers.api_downloaders.iberdrola import Iberdrola


def instance(_config, **_kwargs):
    return Anselmo(_config)


class Anselmo(Iberdrola):
    name = 'anselmo'
    cod_portal = '0118'
    process = None
