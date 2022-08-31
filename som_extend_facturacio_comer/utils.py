from datetime import date


def get_gkwh_atr_price(cursor, uid, polissa, pname, context, with_taxes=False):
    if context is None:
        context = {}

    prod_obj = polissa.pool.get('product.product')
    fact_obj = polissa.pool.get('giscedata.facturacio.factura')

    te_product_id = polissa['tarifa'].get_periodes_producte('te')[pname]
    product_id = fact_obj.get_gkwh_period(cursor, uid, te_product_id, context=context)

    pricelist = polissa['llista_preu']
    price_atr, discount, uom = pricelist.get_atr_price('gkwh', product_id, polissa.fiscal_position_id,
                                    with_taxes=False, direccio_pagament=polissa.direccio_pagament,
                                    titular=polissa.titular, context=context)

    preu_final = price_atr
    if with_taxes:
        preu_final = prod_obj.add_taxes(cursor, uid, te_product_id, price_atr, polissa.fiscal_position_id,
                                        direccio_pagament=polissa.direccio_pagament,
                                        titular=polissa.titular, context=context)

    return preu_final, discount, uom
