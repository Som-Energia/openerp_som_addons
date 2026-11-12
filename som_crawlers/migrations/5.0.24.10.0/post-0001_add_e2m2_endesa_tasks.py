# coding=utf-8
import logging

from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    from tools import config
    if config.updating_all:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("Updating XMLs with new E2 and M2 Endesa crawlers tasks")
    xmls = [
        "data/som_crawlers_task_data.xml",
        "data/som_crawlers_step_data.xml",
    ]
    for xml_w in xmls:
        load_data(
            cursor, 'som_crawlers', xml_w, idref=None, mode='update'
        )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
