# -*- coding: utf-8 -*-


def get_atr_price(cursor, uid, polissa, pname, tipus, context, with_taxes=False):
    from datetime import date
    from datetime import datetime
    import calendar
    if context is None:
        context = {}

    prod_obj = polissa.pool.get('product.product')
    pricelist_obj = polissa.pool.get('product.pricelist')
    pricelistver_obj = polissa.pool.get('product.pricelist.version')
    pricelistitem_obj = polissa.pool.get('product.pricelist.item')
    facturador_obj = polissa.pool.get('giscedata.facturacio.facturador')
    fiscal_pos_obj = polissa.pool.get('account.fiscal.position')
    acc_tax_obj = polissa.pool.get('account.tax')

    product_uom_obj = polissa.pool.get('product.uom')
    if tipus == 'ac':
        periodes_ac = facturador_obj.get_productes_autoconsum(
            cursor, uid, tipus="excedent", context=context
        )
        product_id = periodes_ac[pname]
    else:
        product_id = polissa['tarifa'].get_periodes_producte(tipus)[pname]
    if not context.get('date', False):
        context.update({
            'date': date.today()
        })

    if tipus == 'tp' and not context.get("potencia_anual", False):
        uom_id = product_uom_obj.search(
            cursor, uid, [('factor', '=', 365), ('name', '=', 'kW/dia')])[0]
        if calendar.isleap(datetime.today().year):
            imd_obj = polissa.pool.get('ir.model.data')
            uom_id = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio', 'uom_pot_elec_dia_traspas'
            )[1]
            context['uom'] = uom_id
        context.update({
            'uom': uom_id
        })
    if 'force_pricelist' in context:
        pricelist = pricelist_obj.browse(cursor, uid, context['force_pricelist'])
    else:
        pricelist = polissa['llista_preu']
    discount = 0
    price_surcharge = 0
    if pricelist.visible_discount:
        date_price = date.today().strftime('%Y-%m-%d')
        version = pricelistver_obj.search(cursor, uid,
            [
                ('pricelist_id', '=', pricelist.id),
                '|',
                ('date_start', '=', False),
                ('date_start', '<=', date_price),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', date_price)

            ], order='id', limit=1)
        if version:
            items = pricelistitem_obj.search(
                    cursor, uid, [
                        ('price_version_id', '=', version[0]),
                        ('product_id', '=', product_id)
                    ]
            )
            if items:
                params_to_read = ['price_discount', 'price_surcharge']
                for item in pricelistitem_obj.read(
                        cursor, uid, items, params_to_read):
                    if item['price_discount']:
                        discount = item['price_discount']
                        price_surcharge = item['price_surcharge']
                        break

    price_atr = pricelist_obj.price_get(cursor, uid, [pricelist.id],
                                        product_id, 1,
                                        1,
                                        context)[pricelist.id]
    if discount:
        if discount == -1.0 and price_surcharge:
            discount = 0.0
        else:
            price_atr = price_atr / (1.0 + discount)
            discount = abs(discount)

    if with_taxes:
        preu_final = price_atr
        prod = prod_obj.browse(cursor, uid, product_id)
        for tax in prod.taxes_id:
            fiscal_position = polissa.fiscal_position_id or polissa.titular.property_account_position
            mapped_tax_ids = fiscal_pos_obj.map_tax(cursor, uid, fiscal_position, [tax], context=context)
            if mapped_tax_ids:
                tax_id = mapped_tax_ids[0]
                tax = acc_tax_obj.browse(cursor, uid, tax_id)
            res = tax.compute_from_ids(
                preu_final, 1, polissa.direccio_pagament,
                prod, polissa.titular
            )
            tax_amount = res[0]["amount"]
            if tax_amount:
                preu_final += tax_amount
        return preu_final, discount
    return price_atr, discount