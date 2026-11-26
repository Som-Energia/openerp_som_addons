# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import importlib
from datetime import datetime, timedelta


def get_instance_from_api_module(config_obj, name, process=None, **kwargs):
    if process:
        module = importlib.import_module(
            "som_crawlers.api_downloaders.{}_{}".format(name, process)
        )
    else:
        module = importlib.import_module("som_crawlers.api_downloaders.{}".format(name))
    return module.instance(config_obj, **kwargs)


class BaseApiDownloader(object):

    def __init__(self, config):
        self.config = config
        target_directory = os.path.join('/tmp/outputFiles/', self.name)
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)
        self.target_filename = os.path.join(target_directory, "{}.zip".format(
            datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        ))

    def get_intervals(self):
        final = datetime.now()
        inici = final - timedelta(days=self.config.days_of_margin)

        return inici, final
