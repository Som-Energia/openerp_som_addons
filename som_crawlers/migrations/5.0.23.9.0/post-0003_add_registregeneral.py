# -*- encoding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    #  Actualitzar una part de l'XML (cal posar la id del record)
    logger.info("Updating XMLs")
    load_data_records(
        cursor, 'som_crawlers', 'data/som_crawlers_config_data.xml',
        "registregeneral_conf", mode='update'
    )
    logger.info("XMLs succesfully updated.")

    #  Actualitzar una part de l'XML (cal posar la id del record)
    logger.info("Updating XMLs")
    load_data_records(
        cursor, 'som_crawlers', 'data/som_crawlers_task_data.xml',
        "carregar_registre_general", mode='update'
    )
    logger.info("XMLs succesfully updated.")

    #  Actualitzar una part de l'XML (cal posar la id del record)
    logger.info("Updating XMLs")
    load_data_records(
        cursor, 'som_crawlers', 'data/som_crawlers_step_data.xml',
        "pas_carregar_registre_general", mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
