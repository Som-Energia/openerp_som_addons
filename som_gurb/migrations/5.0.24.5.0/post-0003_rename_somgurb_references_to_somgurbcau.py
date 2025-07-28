# -*- coding: utf-8 -*-
import logging
import pooler


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger("openerp.migration")
    logger.info("Migrating references from som.gurb to som.gurb.cau")
    logger.info("Migrating Sequence")

    pool = pooler.get_pool(cursor.dbname)

    ir_sequence_obj = pool.get("ir.sequence")

    seq_id = ir_sequence_obj.search(
        cursor, 1, [("code", "=", "som.gurb")], context=None
    )

    ir_sequence_obj.write(
        cursor, 1, seq_id, {"code": "som.gurb.cau"}, context=None
    )

    logger.info("Migration completed successfully.")


def down(cursor, installed_version):
    pass


migrate = up
