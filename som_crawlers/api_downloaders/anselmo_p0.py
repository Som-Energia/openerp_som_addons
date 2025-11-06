# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_P0(_config)


class Anselmo_P0(Anselmo):
    name = 'anselmo_p0'
    process = 'P0'
