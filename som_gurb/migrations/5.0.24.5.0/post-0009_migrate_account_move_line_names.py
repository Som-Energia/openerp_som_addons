# -*- coding: utf-8 -*-
import logging
import pooler
from tqdm import tqdm


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Updating existing GURB account.move.line")
    account_move_line_o = pool.get("account.move.line")

    aml_ids = account_move_line_o.search(cursor, 1, [('account_id', '=', 166231)])
    vals = {'name': "Quota del servei GURB Mataró"}
    vals_empresa = {'name': "Quota del servei GURB (empresa) Mataró"}
    for aml_id in tqdm(aml_ids):
        aml = account_move_line_o.browse(cursor, 1, aml_id)
        if "empresa" in aml.name:
            account_move_line_o.write(cursor, 1, aml_id, vals_empresa)
        else:
            account_move_line_o.write(cursor, 1, aml_id, vals)
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
