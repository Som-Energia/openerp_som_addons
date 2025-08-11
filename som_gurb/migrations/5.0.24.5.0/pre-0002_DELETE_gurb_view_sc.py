# coding=utf-8
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)

    logger.info("DANGER!! SERVERS DOWN!!")
    logger.info("Deleting ir_ui_view_sc")

    ui_view_o = pool.get("ir.ui.view")

    gurb_tree_id = ui_view_o.search(cursor, 1, [("name", "=", "som.gurbs.tree")])[0]
    query = "DELETE FROM ui_view_sc_o WHERE view_id = %s"
    cursor.execute(query, (gurb_tree_id,))

    logger.info("NICE!! SERVERS UP!!")


def down(cursor):
    pass


migrate = up
