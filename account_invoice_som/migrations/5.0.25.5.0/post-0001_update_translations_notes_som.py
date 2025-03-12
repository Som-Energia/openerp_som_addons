# -*- encoding: utf-8 -*-
from tools import config
from tools.translate import trans_load


def up(cursor, installed_version):
    if not installed_version or config.updating_all:
        return


    trans_load(cursor, '{}/{}/i18n/es_ES.po'.format(config['addons_path'], 'account_invoice_som'), 'es_ES')

def down(cursor, installed_version):
    pass


migrate = up
