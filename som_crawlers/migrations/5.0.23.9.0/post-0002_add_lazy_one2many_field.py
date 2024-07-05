# -*- encoding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    #  Actualitzar un XML/CSV sencer
    logger.info("Updating XMLs")
    xmls = [
        "views/som_crawlers_task_view.xml",
    ]
    records = [
        "view_som_crawlers_task_form",
    ]
    for xml_w in xmls:
        load_data_records(
            cursor, 'som_crawlers', xml_w, records, idref=None, mode='update'
        )
    logger.info("XMLs succesfully updatd.")


def down(cursor, installed_version):
    pass


migrate = up
