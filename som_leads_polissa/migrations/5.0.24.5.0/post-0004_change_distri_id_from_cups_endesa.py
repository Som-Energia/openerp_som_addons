# -*- coding: utf-8 -*-
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    uid = 1

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Initializing new fields")
    endesa_id = pool.get("res.partner").search(cursor, uid, [('ref', '=', '0031')])[0]
    llista_cups_a_canviar = pool.get("giscedata.cups.ps").search(
        cursor, uid, [('name', 'ilike', 'ES0031')])
    for cups_distri_id in pool.get("giscedata.cups.ps").read(
            cursor, uid, llista_cups_a_canviar, ['distribuidora_id']):
        if cups_distri_id['distribuidora_id'][0] != endesa_id:
            pool.get("giscedata.cups.ps").write(
                cursor, uid, cups_distri_id['id'], {'distribuidora_id': endesa_id})
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
