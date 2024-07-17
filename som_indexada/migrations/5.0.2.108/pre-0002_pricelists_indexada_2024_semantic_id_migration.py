# -*- coding: utf-8 -*-
import logging
from datetime import datetime
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Updating XMLs")

    list_of_xml_name = [("pricelist_indexada_20td_peninsula_2024", "Indexada 2.0TD Península 2024"),
                        ("pricelist_indexada_20td_balears_2024", "Indexada 2.0TD Balears 2024"),
                        ("pricelist_indexada_20td_canaries_2024", "Indexada 2.0TD Canàries 2024"),
                        ("pricelist_indexada_30td_peninsula_2024", "Indexada 3.0TD Península 2024"),
                        ("pricelist_indexada_30td_balears_2024", "Indexada 3.0TD Balears 2024"),
                        ("pricelist_indexada_30td_canaries_2024", "Indexada 3.0TD Canàries 2024"),
                        ("pricelist_indexada_61td_peninsula_2024", "Indexada 6.1TD Península 2024"),
                        ("pricelist_indexada_61td_balears_2024", "Indexada 6.1TD Balears 2024"),
                        ("pricelist_indexada_61td_canaries_2024", "Indexada 6.1TD Canàries 2024"),
                        ("pricelist_indexada_30tdve_peninsula_2024",
                        "Indexada 3.0TVE Península 2024"),
                        ("pricelist_indexada_empresa_peninsula_non_standard_2024",
                        "Indexada Empresa Peninsula 2024"),
                        ("pricelist_indexada_empresa_balears_non_standard_2024",
                        "Indexada Empresa Balears 2024"),
                        ("pricelist_indexada_empresa_canaries_non_standard_2024",
                        "Indexada Empresa Canàries 2024")]

    logger.info("Starting Pricelist Indexada 2024 semantic id creation migration script")
    pool = pooler.get_pool(cursor.dbname)

    model_data_obj = pool.get("ir.model.data")
    pricelist_obj = pool.get("product.pricelist")

    for pricelist in list_of_xml_name:
        pricelist_ids = pricelist_obj.search(cursor, 1, [("name", "=", pricelist[1])])
        if len(pricelist_ids) == 1:
            pricelist_id = pricelist_ids[0]
            today = datetime.today().strftime("%Y-%m-%d")

            model_data_vals = {
                "noupdate": True,
                "name": pricelist[0],
                "module": "som_indexada",
                "model": "product.pricelist",
                "res_id": pricelist_id,
                "date_init": today,
                "date_update": today,
            }

            model_data_obj.create(cursor, 1, model_data_vals)


def down(cursor, installed_version):
    pass


migrate = up
