# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_T1(_config)


class Anselmo_T1(Anselmo):
    name = 'anselmo_t1'
    process = 'T1'
