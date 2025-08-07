# coding=utf-8
import logging
from oopgrade import oopgrade


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')

    logger.info("DANGER!! SERVERS DOWN!!")
    logger.info("Moving som_gurb to som_gurb_cau")

    oopgrade.drop_columns(cursor, [('som_gurb', 'reopening_days'),
                                   ('som_gurb', 'first_opening_days')])
    oopgrade.rename_tables(cursor, ['som_gurb', 'som_gurb_cau'])

    logger.info("NICE!! SERVERS UP!!")


def down(cursor):
    pass


migrate = up
