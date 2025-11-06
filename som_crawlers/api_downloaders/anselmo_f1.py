# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_F1(_config)


class Anselmo_F1(Anselmo):
    name = 'anselmo_f1'
    process = 'F1'
