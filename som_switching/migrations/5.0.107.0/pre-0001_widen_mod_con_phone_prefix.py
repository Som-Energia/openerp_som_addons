# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging


def up(cursor, installed_version):
    if not installed_version:
        return

    cursor.execute(
        """
        SELECT character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
          AND column_name = %s
        """,
        ('giscedata_switching_mod_con_wizard', 'phone_pre')
    )
    result = cursor.fetchone()

    if result and result[0] is not None and result[0] < 4:
        logger = logging.getLogger('openerp.migration')
        logger.info('Widening giscedata_switching_mod_con_wizard.phone_pre')
        cursor.execute(
            """
            ALTER TABLE giscedata_switching_mod_con_wizard
            ALTER COLUMN phone_pre TYPE varchar(4)
            """
        )


def down(cursor, installed_version):
    pass


migrate = up
