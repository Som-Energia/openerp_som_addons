# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pooler
from tools import cache


XML_IDS = (
    'tarifa_20TD_SOM_SOCIAL',
    'tarifa_20TD_SOM_INSULAR_SOCIAL',
    'tarifa_indexada_20TD_peninsula_social',
    'tarifa_indexada_20TD_balears_social',
    'tarifa_indexada_20TD_canaries_social',
)


def migrate(cursor, installed_version):
    pool = pooler.get_pool(cursor.dbname)
    imd = pool.get('ir.model.data')
    pricelist = pool.get('product.pricelist')
    plan = []
    for xml_id in XML_IDS:
        references = imd.search_reader(cursor, 1, [
            ('module', '=', 'som_tarifa_social'), ('name', '=', xml_id),
        ], ['model', 'res_id'])
        if (len(references) != 1
                or references[0]['model'] != 'product.pricelist'
                or not pricelist.search(cursor, 1, [
                    ('id', '=', references[0]['res_id']),
                ], context={'active_test': False})):
            raise ValueError('Social tariff XML has not created %s' % xml_id)
        plan.append((xml_id, references[0]['res_id']))

    # Complete the legacy aliases, including tariffs created by the XML.
    # noupdate protects them when www_som stops loading its old data file.
    for xml_id, pricelist_id in plan:
        ids = imd.search(cursor, 1, [
            ('module', '=', 'www_som'), ('name', '=', xml_id),
        ])
        values = {'res_id': pricelist_id, 'noupdate': True}
        if ids:
            imd.write(cursor, 1, ids, values)
        else:
            values.update({
                'module': 'www_som', 'name': xml_id,
                'model': 'product.pricelist',
            })
            imd.create(cursor, 1, values)

    cache.clean_caches_for_db(cursor.dbname)
