# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_A3(_config)


class Anselmo_A3(Anselmo):
    name = 'anselmo_a3'
    process = 'A3'
