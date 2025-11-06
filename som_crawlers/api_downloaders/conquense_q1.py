# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_Q1(_config)


class Conquense_Q1(Conquense):
    name = 'conquense_q1'
    process = 'Q1'
