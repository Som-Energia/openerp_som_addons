# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    pool = pooler.get_pool(cursor.dbname)
    config_obj = pool.get('som.crawlers.config')
    config_obj._auto_init(cursor, context={'module': 'som_crawlers'})
    load_data(
        cursor, 'som_crawlers', 'views/som_crawlers_config_view.xml',
        idref=None, mode='update',
    )

    data_obj = pool.get('ir.model.data')
    for config_xml_id in ('iberdrola_api_conf', 'conquense_api_conf', 'anselmo_api_conf'):
        config_id = data_obj.get_object_reference(
            cursor, 1, 'som_crawlers', config_xml_id
        )[1]
        config = config_obj.read(cursor, 1, config_id, ['url_portal'])
        if config['url_portal'] in (
            False, '',
            'https://wwwd.i-de.es/pwelconq/services/arq',
            'https://wwwd.i-de.es/pwelconq/services/arq/',
        ):
            config_obj.write(cursor, 1, config_id, {
                'url_portal': 'https://www.i-de.es/pwelconq/services/arq/',
            })

    # Credentials must be entered by an operator, never stored in migrations.
    # Do not reload task data or enable scheduled downloads here.
    logger.info('i-DE API-Key field and configuration view updated')


def down(cursor, installed_version):
    pass


migrate = up
