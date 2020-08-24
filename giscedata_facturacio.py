# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields
from tools.translate import _
from tools import cache
import netsvc
from datetime import datetime


class GiscedataFacturacioFactura(osv.osv):
    """Afegim la funció de Generation kWh.
    """
    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    def unlink(self, cursor, uid, ids, context=None):
        """Return gkwh rights to owner when gkwh invoice is droped"""
        line_obj = self.pool.get('giscedata.facturacio.factura.linia')
        gkwh_lineowner_obj = self.pool.get('generationkwh.invoice.line.owner')
        gkwh_dealer_obj = self.pool.get('generationkwh.dealer')

        invoice_fields = [
            'type', 'polissa_id', 'tarifa_acces_id', 'linies_energia'
        ]

        line_fields = [
            'data_desde', 'data_fins', 'product_id', 'quantity'
        ]

        has_gkwh_rights = False
        for invoice_id in ids:
            rights_dict = self.get_gkwh_shares_dict(
                cursor, uid, invoice_id, context=context
            )
            gkwh_line_ids = self.get_gkwh_lines(
                cursor, uid, invoice_id, context=context
            )
            if gkwh_line_ids:
                has_gkwh_rights = True
                line_obj.unlink(
                    cursor, uid, gkwh_line_ids, context=context
                )
            if has_gkwh_rights:
                invoice_vals = self.read(
                    cursor, uid, invoice_id, invoice_fields, context=context
                )
                if invoice_vals['type'] == 'out_refund':
                    # Re-use rights through dealer when refund invoice
                    # WARNING: The real use may not be the original one

                    contract_id = invoice_vals['polissa_id'][0]
                    fare_id = invoice_vals['tarifa_acces_id'][0]

                    for period_id in rights_dict.keys():
                        quantity = sum([v['kwh'] for v in
                                        rights_dict[period_id]])
                        from_date = max([v['from'] for v in
                                        rights_dict[period_id]])
                        to_date = min([v['to'] for v in
                                      rights_dict[period_id]])

                        gkwh_dealer_obj.use_kwh(
                            cursor,
                            uid,
                            contract_id,
                            from_date,
                            to_date,
                            fare_id,
                            period_id,
                            quantity,
                            context=context
                        )

        return super(GiscedataFacturacioFactura, self).unlink(
            cursor, uid, ids, context
        )

    def anullar(self, cursor, uid, ids, tipus='A', context=None):
        """ Returns gkwh rights on invoice refund """
        gkwh_lineowner_obj = self.pool.get('generationkwh.invoice.line.owner')
        gkwh_dealer_obj = self.pool.get('generationkwh.dealer')
        fact_line_obj = self.pool.get('giscedata.facturacio.factura.linia')

        fields_to_read = ['is_gkwh', 'gkwh_linia_ids', 'type', 'polissa_id',
                          'tarifa_acces_id']
        refund_ids = []
        for inv_vals in self.read(cursor, uid, ids, fields_to_read, context):
            inv_id = inv_vals['id']
            if inv_vals['is_gkwh']:
                # refund gkwh rights
                for glo_id in inv_vals['gkwh_linia_ids']:
                    gkwh_lineowner = gkwh_lineowner_obj.browse(
                        cursor, uid, glo_id, context=context
                    )
                    owner_id = gkwh_lineowner.owner_id.id
                    contract_id = inv_vals['polissa_id'][0]
                    fare_id = inv_vals['tarifa_acces_id'][0]
                    line = gkwh_lineowner.factura_line_id
                    period_id = self.get_fare_period(
                        cursor, uid, line.product_id.id, context=context
                    )
                    # returns rights through dealer
                    gkwh_dealer_obj.refund_kwh(
                        cursor,
                        uid,
                        contract_id,
                        line.data_desde,
                        line.data_fins,
                        fare_id,
                        period_id,
                        line.quantity,
                        owner_id,
                        context=context
                    )
            # refund invoice creation
            refund_id = super(GiscedataFacturacioFactura, self).anullar(
                cursor, uid, [inv_id], tipus, context=context
            )[0]
            refund_ids.append(refund_id)
            # drops invoice lines
            refund_invoice_lines = self.get_gkwh_lines(
                cursor, uid, refund_id, context=context
            )
            if refund_invoice_lines:
                ctx = context.copy()
                ctx.update({'gkwh_manage_rights': False})
                fact_line_obj.unlink(
                    cursor, uid, refund_invoice_lines, context=ctx
                )
            # drop incorrect owner lines
            bad_owner_ids = gkwh_lineowner_obj.search(
                cursor, uid, [('factura_id', '=', refund_id)], context=context
            )
            if bad_owner_ids:
                gkwh_lineowner_obj.unlink(
                    cursor, uid, bad_owner_ids, context=context
                )

            # recreates lines with original invoice rights
            original_invoice_lines_ids = self.get_gkwh_lines(
                cursor, uid, inv_id, context=context
            )

            line_fields = [
                'data_desde', 'data_fins', 'product_id', 'quantity',
                'multi', 'tipus', 'name', 'price_unit_multi', 'tipus',
                'uos_id', 'account_id', 'invoice_line_tax_id',
                'uom_multi_id'
            ]

            for original_line_id in original_invoice_lines_ids:
                line_vals = False
                line_vals = fact_line_obj.read(
                    cursor, uid, original_line_id, line_fields, context=context
                )
                if 'id' in line_vals:
                    del line_vals['id']

                invoice_line_tax_id = [
                    (6, 0, line_vals['invoice_line_tax_id'])
                ]
                line_vals.update({
                    'factura_id': refund_id,
                    'account_id': line_vals['account_id'][0],
                    'invoice_line_tax_id': invoice_line_tax_id,
                    'product_id': line_vals['product_id'][0],
                    'uos_id': line_vals['uos_id'][0],
                })
                refund_line_id = fact_line_obj.create(
                    cursor, uid, line_vals, context
                )

                # creates new owner_line
                original_owner_id = gkwh_lineowner_obj.search(
                    cursor, uid,
                    [('factura_line_id', '=', original_line_id),
                     ('factura_id', '=', inv_id)],
                    context=context
                )[0]
                original_owner_vals = gkwh_lineowner_obj.read(
                    cursor, uid, original_owner_id, ['owner_id'],
                    context=context
                )

                refund_owner_vals = {
                    'owner_id': original_owner_vals['owner_id'][0],
                    'factura_id': refund_id,
                    'factura_line_id': refund_line_id,
                }
                gkwh_lineowner_obj.create(
                    cursor, uid, refund_owner_vals, context=context
                )

        return refund_ids

    def get_gkwh_period(self, cursor, uid, product_id, context=None):
        """" Get's linked Generation kWh period
            product_id: product.product id
        """
        res = None
        per_obj = self.pool.get('giscedata.polissa.tarifa.periodes')

        per_id = self.get_fare_period(cursor, uid, product_id, context=None)

        if per_id:
            res = per_obj.read(
                cursor, uid, per_id, ['product_gkwh_id'], context=context
            )['product_gkwh_id'][0]

        return res

    def get_fare_period(self, cursor, uid, product_id, context=None):
        """" Get's fare period from line product
            product_id: product.product id
        """
        res = None
        per_obj = self.pool.get('giscedata.polissa.tarifa.periodes')

        if isinstance(product_id, (tuple, list)):
            product_id = product_id[0]

        search_vals = [
            '|', ('product_id', '=', product_id),
            ('product_gkwh_id', '=', product_id)
        ]

        per_ids = per_obj.search(
            cursor, uid, search_vals, context=context
        )

        if per_ids:
            return per_ids[0]

        return res

    def get_gkwh_shares_dict(self, cursor, uid, ids, context=None):
        """Returns a dict in the same format returned by dealer use function
        with invoice gkwh rights plus from an to date. key dict is the period
        [{'period_id': {'member_id': member_id
                        'kwh': quantity
                        'from': from date
                        'to': to date
                        }
        }]
        """
        if context is None:
            context = {}

        if isinstance(ids, (tuple, list)):
            ids = ids[0]

        sql = (u"SELECT "
               u"    il.product_id AS product_id, "
               u"    lo.owner_id AS owner_id, "
               u"    SUM(il.quantity) AS quantity ,"
               u"    MIN(fl.data_desde) AS data_desde, "
               u"    MAX(fl.data_fins) AS data_fins "
               u"FROM generationkwh_invoice_line_owner AS lo "
               u"LEFT JOIN giscedata_facturacio_factura_linia AS fl "
               u"    ON lo.factura_line_id = fl.id "
               u"LEFT JOIN account_invoice_line il "
               u"    ON il.id = fl.invoice_line_id "
               u"WHERE lo.factura_id = %(invoice_id)s "
               u"GROUP BY il.product_id, lo.owner_id"
               )

        cursor.execute(sql, {'invoice_id': ids})
        vals = cursor.fetchall()

        fields = ['member_id', 'kwh', 'from', 'to']
        periods = [(v[0], dict(zip(fields, v[1:]))) for v in vals]

        uniq_product_ids = set([p[0] for p in periods])
        product_res = {}.fromkeys(uniq_product_ids, [])

        for p in periods:
            product_res[p[0]].append(p[1])

        res = dict([
            (self.get_fare_period(cursor, uid, k), v)
            for k, v in product_res.items()
        ])

        if context.get('xmlrpc', False):
            res = [(str(k), v) for k, v in res.items()]
        return res

    def apply_gkwh(self, cursor, uid, ids, context=None):
        """Apply gkwh transform"""
        if context is None:
            context = {}

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        invlines_obj = self.pool.get('giscedata.facturacio.factura.linia')
        pricelist_obj = self.pool.get('product.pricelist')
        partner_obj = self.pool.get('res.partner')

        gkwh_lineowner_obj = self.pool.get('generationkwh.invoice.line.owner')
        gkwh_dealer_obj = self.pool.get('generationkwh.dealer')
        inv_fields = ['polissa_id', 'data_inici', 'data_final', 'llista_preu',
                      'tarifa_acces_id', 'linies_energia', 'type']

        line_fields = ['data_desde', 'data_fins', 'product_id', 'quantity',
                       'multi', 'tipus', 'name', 'price_unit_multi', 'uos_id',
                       'account_id', 'invoice_line_tax_id', 'uom_multi_id'
                       ]

        for inv_id in ids:
            # Test if is client invoice (out_invoice, out_refund)
            # Test if contract is gkwh enabled
            inv_data = self.read(cursor, uid, inv_id, inv_fields, context)

            contract_id = inv_data['polissa_id'][0]
            start_date = inv_data['data_inici']
            end_date = inv_data['data_final']
            pricelist = inv_data['llista_preu'][0]

            if inv_data['type'] not in ['out_invoice', 'out_refund']:
                return

            is_gkwh = gkwh_dealer_obj.is_active(
                cursor, uid, contract_id, start_date, end_date, context=context
            )

            if not is_gkwh:
                return

            # Get energy periods
            for line_id in inv_data['linies_energia']:
                line_vals = False
                line_vals = invlines_obj.read(
                    cursor, uid, line_id, line_fields, context=context
                )
                line_product_id = line_vals['product_id'][0]

                # GkWh invoice line creation
                product_gkwh_id = self.get_gkwh_period(
                    cursor, uid, line_product_id, context=context
                )

                vals = line_vals.copy()

                if 'id' in vals:
                    del vals['id']

                invoice_line_tax_id = [
                    (6, 0, line_vals['invoice_line_tax_id'])
                ]

                price_unit = pricelist_obj.price_get(
                    cursor, uid, [pricelist], product_gkwh_id, 1,
                    context={'date': end_date}
                )[pricelist]

                # Get available gkwh rights
                # returns a list of rights x member
                fare = inv_data['tarifa_acces_id'][0]
                period = self.get_fare_period(
                    cursor, uid, line_product_id, context=context
                )
                line_quantity = line_vals['quantity']

                gkwh_quantity_dict = gkwh_dealer_obj.use_kwh(
                    cursor, uid, contract_id, start_date, end_date, fare,
                    period, line_quantity
                )

                vals.update({
                    'factura_id': inv_id,
                    'data_desde': line_vals['data_desde'],
                    'data_fins': line_vals['data_fins'],
                    'product_id': product_gkwh_id,
                    'price_unit_multi': price_unit,
                    'account_id': vals['account_id'][0],
                    'invoice_line_tax_id': invoice_line_tax_id,
                    'uos_id': line_vals['uos_id'][0],
                })
                # original line quantity counter
                new_quantity = line_quantity
                for gkwh_line in gkwh_quantity_dict:
                    gkwh_quantity = gkwh_line['kwh']
                    gkwh_owner_id = gkwh_line['member_id']

                    gwkh_owner_name = partner_obj.read(
                        cursor, uid, gkwh_owner_id, ['name'], context=context
                    )['name']

                    # substract from original line quantity
                    new_quantity -= gkwh_quantity

                    invlines_obj.write(
                        cursor, uid, line_id, {'quantity': new_quantity}
                    )

                    # create gkwh line
                    vals.update({
                        'quantity': gkwh_quantity,
                        'name': _(u'{0} GkWh').format(line_vals['name']),
                    })
                    iline_id = invlines_obj.create(cursor, uid, vals, context)
                    # owner line object creation
                    gkwh_lineowner_obj.create(
                        cursor, uid, {
                            'factura_id': inv_id,
                            'factura_line_id': iline_id,
                            'owner_id': gkwh_owner_id
                        }
                    )

            self.button_reset_taxes(cursor, uid, [inv_id], context=context)

    def get_gkwh_lines(self, cursor, uid, ids, context=None):
        """ Returns a id list of giscedata.facturacio.factura.linia with
            gkwh products
        """
        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        line_obj = self.pool.get('giscedata.facturacio.factura.linia')

        res = []
        fields_to_read = ['linies_energia']
        inv_vals = self.read(cursor, uid, ids, fields_to_read, context)
        if inv_vals['linies_energia']:
            is_gkwh = line_obj.is_gkwh(cursor, uid, inv_vals['linies_energia'])
            line_ids = [l for l, v in is_gkwh.items() if v]
            return line_ids
        return res

    def _search_is_gkwh(self, cursor, uid, obj, name, args, context=None):
        """Search function for is_gkwh"""
        if not args:
            return [('id', '=', 0)]

        cursor.execute(
            'SELECT distinct factura_id FROM generationkwh_invoice_line_owner'
        )

        gkwh_ids = [t[0] for t in cursor.fetchall()]

        operator = 'in'
        if not args[0][2]:
            # search for False
            operator = 'not in'
        return [('id', operator, gkwh_ids)] 

    def _ff_is_gkwh(self, cursor, uid, ids, field_name, arg, context=None):
        """Returns true if invoice has gkwh lines"""
        if not ids:
            return []
        res = dict([(i, False) for i in ids])

        vals = self.read(cursor, uid, ids, ['gkwh_linia_ids'])
        for val in vals:
            res.update({val['id']: bool(val['gkwh_linia_ids'])})

        return res

    _columns = {
        'gkwh_linia_ids': fields.one2many(
            'generationkwh.invoice.line.owner', 'factura_id',
            'Propietaris Generation kWH', readonly=True
        ),
        'is_gkwh': fields.function(
            _ff_is_gkwh,
            method=True,
            string='Te Generation', type='boolean',
            fnct_search=_search_is_gkwh
        )
    }

GiscedataFacturacioFactura()


class GiscedataFacturacioFacturador(osv.osv):
    """Sobreescrivim el mètode fact_via_lectures per aplicar GkWh.
    """
    _name = 'giscedata.facturacio.facturador'
    _inherit = 'giscedata.facturacio.facturador'


    def elimina_ajustar_saldo_excedents_autoconsum(self, cursor, uid, factura_id, context=None):
        flinia_o = self.pool.get("giscedata.facturacio.factura.linia")
        imd_o = self.pool.get("ir.model.data")
        producte_ajust_autoconsum = product_id = imd_o.get_object_reference(cursor, uid, "giscedata_facturacio_comer", 'saldo_excedents_autoconsum')[1]
        l_autoc = flinia_o.search(cursor, uid, [('tipus', '=', 'generacio'), ('factura_id', '=', factura_id), ('product_id', '=', producte_ajust_autoconsum)])
        if len(l_autoc):
            flinia_o.unlink(cursor, uid, l_autoc)
            return True
        return False

    def reaplica_ajustar_saldo_excedents_autoconsum(self, cursor, uid, factura_ids, context=None):
        if not isinstance(factura_ids, (tuple, list)):
            factura_ids = [factura_ids]
        for factura_id in factura_ids:
            self.elimina_ajustar_saldo_excedents_autoconsum(cursor, uid, factura_id, context=context)
            self.ajustar_saldo_excedents_autoconsum(cursor, uid, factura_id, context=context)
        return True

    def fact_via_lectures(self, cursor, uid, polissa_id, lot_id, context=None):
        factures = super(GiscedataFacturacioFacturador,
                         self).fact_via_lectures(cursor, uid, polissa_id,
                                                 lot_id, context)
        factura_obj = self.pool.get('giscedata.facturacio.factura')
        factura_obj.apply_gkwh(cursor, uid, factures, context)
        self.reaplica_ajustar_saldo_excedents_autoconsum(cursor, uid, factures, context)
        factura_obj.button_reset_taxes(cursor, uid, factures, context=context)
        return factures


GiscedataFacturacioFacturador()


class GiscedataFacturacioFacturaLinia(osv.osv):
    """Generation kwH invoice line management"""

    _name = 'giscedata.facturacio.factura.linia'
    _inherit = 'giscedata.facturacio.factura.linia'

    @cache()
    def get_gkwh_products(self, cursor, uid, context=None):
        """Returns generation kwh products list"""
        pcat_obj = self.pool.get('product.category')
        product_obj = self.pool.get('product.product')

        cat_ids = pcat_obj.search(
            cursor, uid, [('name', '=', 'Generation kWh')]
        )
        return product_obj.search(cursor, uid, [('categ_id', 'in', cat_ids)])

    def is_gkwh(self, cursor, uid, ids, context=None):
        """Checks invoice line is gkwh"""
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        res = dict([(i, False) for i in ids])

        # check if product is gkwh
        l_vals = self.read(cursor, uid, ids, ['product_id'], context=context)
        gkwh_products = self.get_gkwh_products(cursor, uid)
        for l in l_vals:
            if l['product_id'] and l['product_id'][0] in gkwh_products:
                res[l['id']] = True
        return res

    def unlink(self, cursor, uid, ids, context=None):
        """Return gkwh rights to owner when gkwh invoice line is droped"""
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        gkwh_lineowner_obj = self.pool.get('generationkwh.invoice.line.owner')
        gkwh_dealer_obj = self.pool.get('generationkwh.dealer')

        is_gkwh_vals = self.is_gkwh(cursor, uid, ids, context=context)
        for line_id, value in is_gkwh_vals.items():
            if value:
                # reads owner
                line = self.browse(cursor, uid, line_id, context=context)
                glo_ids = gkwh_lineowner_obj.search(
                    cursor, uid, [('factura_line_id', '=', line_id)]
                )
                if not context.get('gkwh_manage_rights', True):
                    # do not refund/use rights
                    if glo_ids:
                        gkwh_lineowner_obj.unlink(cursor, uid, glo_ids)
                    continue
                if not glo_ids:
                    owner_id = 1
                else:
                    glo_vals = gkwh_lineowner_obj.read(
                        cursor, uid, glo_ids, ['owner_id']
                    )[0]
                    owner_id = glo_vals['owner_id'][0]
                invoice_type = line.factura_id.type
                contract_id = line.factura_id.polissa_id.id
                fare_id = line.factura_id.tarifa_acces_id.id
                period_id = fact_obj.get_fare_period(
                    cursor, uid, line.product_id.id, context=context
                )
                if invoice_type in ['out_invoice', 'in_invoice']:
                    # refunds rights through dealer
                    if glo_ids:
                        gkwh_lineowner_obj.unlink(cursor, uid, glo_ids)
                    gkwh_dealer_obj.refund_kwh(
                        cursor,
                        uid,
                        contract_id,
                        line.data_desde,
                        line.data_fins,
                        fare_id,
                        period_id,
                        line.quantity,
                        owner_id,
                        context=context
                    )
                elif invoice_type in ['out_refund', 'out_refund']:
                    # The rights re-use has to be done in invoice scope
                    # Re-use rights through dealer when refund invoice
                    # WARNING: The real use may not be the original one
                    if glo_ids:
                        gkwh_lineowner_obj.unlink(cursor, uid, glo_ids)
                    # gkwh_dealer_obj.use_kwh(
                    #     cursor,
                    #     uid,
                    #     contract_id,
                    #     line.data_desde,
                    #     line.data_fins,
                    #     fare_id,
                    #     period_id,
                    #     line.quantity,
                    #     context=context
                    # )

        return super(GiscedataFacturacioFacturaLinia, self).unlink(
            cursor, uid, ids, context
        )

GiscedataFacturacioFacturaLinia()

# vim: et ts=4 sw=4
