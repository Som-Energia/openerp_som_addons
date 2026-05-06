import logging
from oopgrade.oopgrade import add_columns


def up(cursor, installed_version):
    if not installed_version:
        return
    logger = logging.getLogger('openerp.migration')

    add_columns(cursor,
                {'som_template': [('data_baixa', 'date')]})

    logger.info('Done')


migrate = up
