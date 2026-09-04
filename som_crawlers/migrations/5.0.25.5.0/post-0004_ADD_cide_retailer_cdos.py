# -*- coding: utf-8 -*-
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    load_data(
        cursor,
        "som_crawlers",
        "data/som_crawlers_config_data.xml",
        idref=None,
        mode="update",
    )


def down(cursor, installed_version):
    pass


migrate = up
