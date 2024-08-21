import logging
from tools import config
from tools.translate import trans_load


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    module_name = 'som_polissa_condicions_generals'

    logger.info("Updating translations")
    trans_load(cursor, '{}/{}/i18n/ca_ES.po'.format(config['addons_path'], module_name), 'es_ES')
    logger.info("Translations succesfully updated.")


def down(cursor, installed_version):
    pass


migrate = up
