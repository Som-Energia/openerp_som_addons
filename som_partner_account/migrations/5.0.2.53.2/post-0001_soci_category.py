# -*- coding: utf-8 -*-
"""Esborra la category nova si ja n'existeix una de vella"""

import netsvc
import pooler


def migrate(cursor, installed_version):
    uid = 1
    logger = netsvc.Logger()

    pool = pooler.get_pool(cursor.dbname)
    cat_obj = pool.get("res.partner.category")
    imd_obj = pool.get("ir.model.data")

    soci_cat_ids = cat_obj.search(cursor, uid, [("name", "=", "Soci")])

    if len(soci_cat_ids) > 1:
        # Old Soci category existent:
        logger.notifyChannel(
            "migration", netsvc.LOG_INFO, "Ja existeix Soci Category antiga. %s" % soci_cat_ids
        )
        imd_data = imd_obj._get_obj(cursor, uid, "som_partner_account", "res_partner_category_soci")
        imd_id = imd_obj._get_id(cursor, uid, "som_partner_account", "res_partner_category_soci")
        soci_nou = imd_data.id
        soci_vell = [c for c in soci_cat_ids if c != soci_nou][0]
        cat_obj.unlink(cursor, uid, soci_nou)
        logger.notifyChannel(
            "migration", netsvc.LOG_INFO, "Esborrat Soci Category nou: %s" % soci_nou
        )
        imd_obj.write(cursor, uid, imd_id, {"res_id": soci_vell})
        logger.notifyChannel(
            "migration",
            netsvc.LOG_INFO,
            "Modificat ir_model_data amb Soci Category vell: %s" % soci_vell,
        )
    else:
        # No previous Soci Category
        logger.notifyChannel(
            "migration",
            netsvc.LOG_INFO,
            "Soci Category no repetit. " "Ja existia o creat correctament %s " % soci_cat_ids[0],
        )

    logger.notifyChannel("migration", netsvc.LOG_INFO, "Soci Category Creat correctament")
