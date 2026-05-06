# -*- coding: utf-8 -*-
import os
import importlib
import socket
from datetime import datetime, timedelta


def get_instance_from_api_module(config_obj, name, process=None):
    if process:
        module = importlib.import_module("som_crawlers.api_downloaders.{}_{}".format(name, process))
    else:
        module = importlib.import_module("som_crawlers.api_downloaders.{}".format(name))
    return module.instance(config_obj)


class BaseApiDownloader(object):

    def __init__(self, config):
        self.config = config
        target_directory = os.path.join('/tmp/outputFiles/', self.name)
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)
        self.target_filename = os.path.join(target_directory, "{}.zip".format(
            datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        ))

    def is_production(self):
        return socket.gethostname() in [
            'erp01', 'erpwork01', 'erpwork02', 'erpwork03', 'erpwork04', 'erpwork05']

    def get_intervals(self):
        if self.is_production():
            final = datetime.now()
        else:
            final = datetime(2025, 8, 15)
        inici = final - timedelta(self.config.days_of_margin)

        return inici, final
