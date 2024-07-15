# -*- coding: utf-8 -*-
import logging
from oopgrade.oopgrade import load_data_records


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating XMLs")

    list_of_records = ["pricelist_indexada_20td_peninsula_2024",
                       "pricelist_indexada_20td_balears_2024",
                       "pricelist_indexada_20td_canaries_2024",
                       "pricelist_indexada_30td_peninsula_2024",
                       "pricelist_indexada_30td_balears_2024",
                       "pricelist_indexada_30td_canaries_2024",
                       "pricelist_indexada_61td_peninsula_2024",
                       "pricelist_indexada_61td_balears_2024",
                       "pricelist_indexada_61td_canaries_2024",
                       "pricelist_indexada_empresa_peninsula_non_standard_2024",
                       "pricelist_indexada_empresa_balears_non_standard_2024",
                       "pricelist_indexada_empresa_canaries_non_standard_2024"]

    load_data_records(
        cursor,
        'som_indexada',
        'product_pricelist_data.xml',
        list_of_records,
        mode='update'
    )
    logger.info("XMLs succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
