# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

import pooler
from tools import cache


TARIFFS = (
    ('tarifa_20TD_SOM_SOCIAL', u'2.0TD_SOM_SOCIAL'),
    ('tarifa_20TD_SOM_INSULAR_SOCIAL', u'2.0TD_SOM_INSULAR_SOCIAL'),
    ('tarifa_indexada_20TD_peninsula_social',
     u'Indexada 2.0TD Península SOCIAL'),
    ('tarifa_indexada_20TD_balears_social', u'Indexada 2.0TD Balears SOCIAL'),
    ('tarifa_indexada_20TD_canaries_social', u'Indexada 2.0TD Canàries SOCIAL'),
)


def migrate(cursor, installed_version):
    pool = pooler.get_pool(cursor.dbname)
    imd = pool.get('ir.model.data')
    pricelist = pool.get('product.pricelist')
    context = {'active_test': False}
    logger = logging.getLogger('openerp.migration')
    plan = []

    # Validate all five tariffs before changing metadata. Valid XML identities
    # take precedence; exact-name recovery is only for missing or broken IDs.
    for xml_id, name in TARIFFS:
        references = imd.search_reader(cursor, 1, [
            ('module', 'in', ['www_som', 'som_tarifa_social']),
            ('name', '=', xml_id),
        ], ['module', 'model', 'res_id', 'noupdate'])
        if any(ref['model'] != 'product.pricelist' for ref in references):
            raise ValueError('Unexpected model for social tariff ID %s' % xml_id)
        ids = pricelist.search(cursor, 1, [
            ('id', 'in', [ref['res_id'] for ref in references]),
        ], context=context)
        if len(ids) > 1:
            raise ValueError('Conflicting social tariff IDs for %s: %s' % (
                xml_id, ids,
            ))
        if not ids:
            ids = pricelist.search(
                cursor, 1, [('name', '=', name)], context=context,
            )
            if len(ids) > 1:
                raise ValueError('Ambiguous social tariff recovery for %s: %s'
                                 % (xml_id, ids))
        plan.append((xml_id, ids[0] if ids else None, references))

    for xml_id, pricelist_id, references in plan:
        if pricelist_id is None:
            # The XML will create the missing tariff. Only discard dangling
            # metadata in the new namespace; never delete business records.
            for ref in references:
                if ref['module'] == 'som_tarifa_social':
                    imd.unlink(cursor, 1, [ref['id']])
                else:
                    imd.write(cursor, 1, [ref['id']], {'noupdate': True})
            logger.info('Social tariff %s will be created by XML', xml_id)
            continue

        for module in ('www_som', 'som_tarifa_social'):
            values = {
                'res_id': pricelist_id, 'noupdate': module == 'www_som',
            }
            existing = next((ref for ref in references
                             if ref['module'] == module), None)
            if existing:
                if any(existing[key] != value
                       for key, value in values.items()):
                    imd.write(cursor, 1, [existing['id']], values)
            else:
                values.update({
                    'module': module, 'name': xml_id,
                    'model': 'product.pricelist',
                })
                imd.create(cursor, 1, values)
        logger.info('Social tariff %s reuses pricelist %s', xml_id, pricelist_id)

    cache.clean_caches_for_db(cursor.dbname)
