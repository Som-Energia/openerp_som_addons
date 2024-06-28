# -*- encoding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    #  Actualitzar un XML/CSV sencer
    logger.info("Updating XMLs")
    xmls = [
        "som_crawlers_step_data.xml",
        "som_crawlers_task_data.xml",
    ]
    for xml_w in xmls:
        load_data(
            cursor, 'som_crawlers', xml_w, idref=None, mode='update'
        )
    logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
