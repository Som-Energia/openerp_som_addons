# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_R0(_config)


class Anselmo_R0(Anselmo):
    name = 'anselmo_r0'
    process = 'R0'
