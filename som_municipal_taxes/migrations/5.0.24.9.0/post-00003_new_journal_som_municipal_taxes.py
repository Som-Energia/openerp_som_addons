# -*- encoding: utf-8 -*-
import logging
import pooler
from oopgrade.oopgrade import load_data


def up(cursor, installed_version):
    if not installed_version:
        return

    logger = logging.getLogger('openerp.migration')
    logger.info("Creating pooler")
    pool = pooler.get_pool(cursor.dbname)
    uid = 1

    views = [
        'data/som_municipal_taxes_data.xml',
        'wizard/wizard_creacio_remesa_pagament_taxes.xml',
        'wizard/wizard_presentacio_redsaras.xml',
    ]
    for view in views:
        # Crear les diferents vistes
        logger.info("Updating XML {}".format(view))
        load_data(cursor, 'som_municipal_taxes', view, idref=None, mode='update')
        logger.info("XMLs succesfully updatd.")

    logger.info("Creating partner_address and vat for City Hall")
    # Crear partner_address i vat per l'ajuntament
    partner_obj = pool.get('res.partner')
    partner_address_obj = pool.get('res.partner.address')
    category_id = pool.get('ir.model.data').get_object_reference(
        cursor, uid, 'som_municipal_taxes', 'res_partner_category_ajuntament')
    # Search for a partner with category res_partner_category_ajuntament
    partner_ids = partner_obj.search(cursor, uid, [('category_id', '=', category_id[1])])
    for patner_id in partner_ids:
        partner = partner_obj.browse(cursor, uid, patner_id)
        if not partner.vat:
            partner.write({
                'vat': 'ES00000001R',
                'comment': 'NIF fictici ES00000001R per a l\'ajuntament necessari per fer les \
                    factures del 1,5%. Si necessiteu el real, el podeu \
                    posar\n\n {}'.format(partner.comment),
            })
        if not partner_address_obj.search(cursor, uid, [('partner_id', '=', partner.id)]):
            partner_address_obj.create(cursor, uid, {
                'partner_id': partner.id,
                'name': partner.name,
                'is_default': True,
            })


def down(cursor, installed_version):
    pass


migrate = up
