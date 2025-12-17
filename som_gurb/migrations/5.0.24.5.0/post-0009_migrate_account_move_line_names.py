import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("Updating XML files")
    account_move_line_o = pool.get("account.move.line")

    aml_ids = account_move_line_o.search(cursor, 1, [('account_id', '=', 166231)])
    for aml_id in aml_ids:
        account_move_line_o.write(cursor, 1, aml_id, {'name': 'Quota del servei GURB Mataró'})
    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
