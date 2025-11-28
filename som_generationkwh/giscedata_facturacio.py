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
        gkwh_rightusage_obj = self.pool.get('generationkwh.right.usage.line')
        gkwh_dealer_obj = self.pool.get('generationkwh.dealer')
        fact_line_obj = self.pool.get('giscedata.facturacio.factura.linia')

        fields_to_read = ['is_gkwh', 'gkwh_linia_ids', 'type', 'polissa_id',
                          'tarifa_acces_id']
        refund_ids = []
        refunded_dict = {}
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
                    refunded_dates = gkwh_dealer_obj.refund_kwh(
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
                    refunded_dict[gkwh_lineowner.factura_line_id.id] = refunded_dates['unusage']
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
                original_factura_line_id = line_vals['id']
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
                #No group gkwh lines
                ctx = context.copy()
                ctx['group_line'] = False
                refund_line_id = fact_line_obj.create(
                    cursor, uid, line_vals, context=ctx
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
                lineowner_id = gkwh_lineowner_obj.create(
                    cursor, uid, refund_owner_vals, context=context
                )

                for k,v in refunded_dict[original_factura_line_id].items():
                    gkwh_rightusage_obj.create(
                        cursor, uid, {
                            'datetime': k, 'quantity': v,
                            'line_owner': lineowner_id
                        }
                    )

        return refund_ids

    def get_energy_product_from_gkwh(self, cursor, uid, gkwh_product_id, context=None):
        """" Get's atr product from Generation kWh product
            product_id: product.product id
        """
        res = None
        per_obj = self.pool.get('giscedata.polissa.tarifa.periodes')

        if isinstance(gkwh_product_id, (tuple, list)):
            gkwh_product_id = gkwh_product_id[0]

        search_vals = [
            ('product_gkwh_id', '=', gkwh_product_id)
        ]

        per_ids = per_obj.search(
            cursor, uid, search_vals, context=context
        )

        if per_ids:
            res = per_obj.read(cursor, uid, per_ids[0], ['product_id'])['product_id'][0]

        return res

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
        product_res = {k: [] for k in uniq_product_ids}

        for p in periods:
            product_res[p[0]].append(p[1])

        res = dict([
            (self.get_fare_period(cursor, uid, k), v)
            for k, v in product_res.items()
        ])

        if context.get('xmlrpc', False):
            res = [(str(k), v) for k, v in res.items()]
        return res

    def get_lines_in_extralines(self, cursor, uid, inv_id, pol_id):
        extra_obj = self.pool.get('giscedata.facturacio.extra')
        extra_ids = extra_obj.search(cursor, uid,[
                ('polissa_id', '=', pol_id),
                ('factura_ids', 'in', inv_id),
            ])
        extra_linia_datas = extra_obj.read(cursor, uid,
                extra_ids,
                ['factura_linia_ids']
            )

        factura_linia_ids = []

        for eld in extra_linia_datas:
            factura_linia_ids.extend(eld['factura_linia_ids'])
        return factura_linia_ids

    def get_real_energy_lines(self, cursor, uid, inv_id, pol_id, linies_energia_ids):
        product_obj = self.pool.get('product.product')
        invline_obj = self.pool.get('giscedata.facturacio.factura.linia')
        maj_product = product_obj.search(cursor, uid, [('default_code','=', 'RMAG')])
        if maj_product:
            maj_product = maj_product[0]
        else:
            maj_product = False

        real_energy = []
        lines_extra_ids = self.get_lines_in_extralines(cursor, uid, inv_id, pol_id)
        for l_id in linies_energia_ids:
            if l_id not in lines_extra_ids:
                line = invline_obj.browse(cursor, uid, l_id)
                if line.product_id.id == maj_product:
                    continue
                real_energy.append(l_id)
        return real_energy

    def apply_gkwh(self, cursor, uid, ids, context=None):
        """Apply gkwh transform"""
        if context is None:
            context = {}

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        invlines_obj = self.pool.get('giscedata.facturacio.factura.linia')
        pricelist_obj = self.pool.get('product.pricelist')
        partner_obj = self.pool.get('res.partner')
        gkwh_rightusage_obj = self.pool.get('generationkwh.right.usage.line')

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
            real_energy_lines_ids = self.get_real_energy_lines(
                cursor, uid, inv_id, contract_id, inv_data['linies_energia']
            )
            for line_id in real_energy_lines_ids:
                line_vals = False
                line_vals = invlines_obj.read(
                    cursor, uid, line_id, line_fields, context=context
                )
                end_date_line = line_vals['data_fins']
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
                    context={'date': end_date_line}
                )[pricelist]

                # Get available gkwh rights
                # returns a list of rights x member
                fare = inv_data['tarifa_acces_id'][0]
                period = self.get_fare_period(
                    cursor, uid, line_product_id, context=context
                )
                line_quantity = line_vals['quantity']

                # TODO: Can we check if this is a regularization line?
                if line_quantity < 0:
                    continue

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
                    #No group gkwh lines
                    ctx = context.copy()
                    ctx['group_line'] = False
                    iline_id = invlines_obj.create(cursor, uid, vals, context=ctx)
                    # owner line object creation
                    lineowner_id = gkwh_lineowner_obj.create(
                        cursor, uid, {
                            'factura_id': inv_id,
                            'factura_line_id': iline_id,
                            'owner_id': gkwh_owner_id
                        }
                    )
                    for k,v in gkwh_line['usage'].items():
                        gkwh_rightusage_obj.create(
                            cursor, uid, {
                                'datetime': k, 'quantity': v,
                                'line_owner': lineowner_id
                            }
                        )
            self.update_maj_quantity(cursor, uid, inv_id, context)

    def update_maj_quantity(self, cursor, uid, inv_id, context):
        rmag_lines_ids = self.get_rmag_lines(cursor, uid, inv_id, context)
        if not rmag_lines_ids:
            return

        line_obj = self.pool.get('giscedata.facturacio.factura.linia')
        rmag_line = line_obj.browse(cursor, uid, rmag_lines_ids[0])

        cfg_obj = self.pool.get('res.config')

        start_date_mecanisme_ajust_gas = cfg_obj.get(
           cursor, uid, 'start_date_mecanisme_ajust_gas', '2022-10-01'
        )
        end_date_mecanisme_ajust_gas = cfg_obj.get(
            cursor, uid, 'end_date_mecanisme_ajust_gas', '2099-12-31'
        )
        all_gkwh_lines_ids = self.get_gkwh_lines(cursor, uid, inv_id, context)
        substract_from_maj_line_ids = line_obj.search(cursor, uid,
            [('id', 'in', all_gkwh_lines_ids), ('data_desde', '>=', start_date_mecanisme_ajust_gas),
            ('data_fins','<=', end_date_mecanisme_ajust_gas)]
        )
        if substract_from_maj_line_ids:
            rmag_original_quantity = rmag_line.quantity
            gkwh_data = line_obj.read(cursor, uid, substract_from_maj_line_ids, ['quantity'])
            new_quantity = rmag_original_quantity - sum([x['quantity'] for x in gkwh_data])
            line_obj.write(cursor, uid, rmag_line.id, {'quantity': new_quantity})

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

    def get_rmag_lines(self, cursor, uid, ids, context=None):
        """ Returns a id list of giscedata.facturacio.factura.linia with
            RMAG products
        """
        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        line_obj = self.pool.get('giscedata.facturacio.factura.linia')

        res = []
        fields_to_read = ['linies_energia']
        inv_vals = self.read(cursor, uid, ids, fields_to_read, context)
        if inv_vals['linies_energia']:
            is_rmag = line_obj.is_rmag(cursor, uid, inv_vals['linies_energia'])
            line_ids = [l for l, v in is_rmag.items() if v]
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
        if isinstance(polissa_id, (tuple, list)):
            polissa_id = polissa_id[0]

        factura_obj = self.pool.get('giscedata.facturacio.factura')
        polissa_obj = self.pool.get('giscedata.polissa')
        can_have_gkwh = polissa_obj.read(cursor, uid, polissa_id, ['te_assignacio_gkwh'])['te_assignacio_gkwh']
        if can_have_gkwh:
            factura_obj.apply_gkwh(cursor, uid, factures, context)
            self.reaplica_ajustar_saldo_excedents_autoconsum(cursor, uid, factures, context)
        return factures

    def create_discount_lines_for_rd_17_2021(self, cursor, uid, fact_ids, context=None):
        if context is None:
            context = {}

        fact_obj = self.pool.get('giscedata.facturacio.factura')
        line_obj = self.pool.get('giscedata.facturacio.factura.linia')
        pricelist_obj = self.pool.get('product.pricelist')
        imd_obj = self.pool.get('ir.model.data')

        tarifes_elec_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'pricelist_tarifas_electricidad'
        )[1]

        discount_pricelist_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer', 'pricelist_precios_descuento_rd_17_2021'
        )[1]

        ctx = context.copy()
        for factura_id in fact_ids:
            factura = fact_obj.browse(cursor, uid, factura_id, context=ctx)

            # IF there's a previous base_pricelist_lit where delete it
            if ctx.get('base_pricelist_list', False):
                ctx.update({'base_pricelist_list': {}})

            periodes_energia = [l.product_id for l in factura.linia_ids if l.tipus == 'energia' and not l.is_gkwh()[l.id]]
            num_periodes = len(list(set(periodes_energia)))
            llista_preus = factura.llista_preu
            mode_facturacio = factura.polissa_id.mode_facturacio
            is_indexada_and_uses_cargos = self.is_indexada_and_uses_cargos(cursor, uid, factura, context=context)
            force_full_discount = self.has_to_force_full_discount(cursor, uid, factura, context=context)
            if mode_facturacio == 'pvpc':
                ctx['pricelist_base_price'] = 0.0  # Dummy base price to avoid error
            for line in factura.linia_ids:
                if line.tipus in ('energia', 'potencia') and line.data_desde >= "2021-06-01" and line.data_fins <= "2021-12-31" and not line.isdiscount:
                    # let's get the price in order to get the base_pricelist_lit for his product
                    product_id = line.product_id.id
                    if line.is_gkwh()[line.id]:
                        product_id = fact_obj.get_energy_product_from_gkwh(cursor, uid, product_id)

                    ctx.update({'date': line.data_desde, 'uom': line.uos_id.id, 'base_pricelist_list': {}})
                    price = pricelist_obj.price_get(
                        cursor, uid, [llista_preus.id],
                        line.product_id.id, line.quantity, context=ctx
                    )
                    discount_to_apply = 0.0

                    if force_full_discount or \
                        (line.tipus == 'energia' and (mode_facturacio == 'pvpc' or (
                            mode_facturacio == 'index' and is_indexada_and_uses_cargos))):
                        discount_to_apply = 1.0
                    else:
                        # List of pricelist referenced in the price list item recursively
                        base_pricelist_list = ctx.get('base_pricelist_list', False)
                        if base_pricelist_list and base_pricelist_list.get(tarifes_elec_id, False):
                            discount_to_apply = 1 + base_pricelist_list[tarifes_elec_id][0]

                    total_discount = 0.0
                    if line.tipus == 'energia' and num_periodes == 1 and line.data_desde >= "2021-09-16" and line.data_fins <= '2021-12-31':
                        try:
                            discount_price = pricelist_obj.price_get(
                                cursor, uid, [discount_pricelist_id],
                                product_id, 1, context=ctx
                            )
                        except:
                            raise NotImplementedError(
                                _(u"Cálcul del preu de descompte segons RD 17/2021 no implementat "
                                  u"per a la tarifa {}").format(factura.polissa_id.tarifa.name))
                        if discount_price:
                            total_discount = discount_price[discount_pricelist_id]
                    elif line.tipus == 'energia' and num_periodes == 2:
                        raise NotImplementedError(_(u"Cálcul del preu de descompte segons RD 17/2021 "
                                                    u"per a 2 periodes no implementat"))
                    else:
                        total_discount = self.get_discount_line_total_discount(cursor, uid, product_id, factura, context=ctx)

                    if total_discount:
                        vals = self.get_discount_line_vals(cursor, uid, line, context=context)
                        vals.update({'force_price': total_discount})

                        if discount_to_apply:
                            vals.update({'discount': discount_to_apply * 100.0})

                        ctx_crear_linia = context.copy()
                        ctx_crear_linia.update({'force_not_showing_discount': True})
                        line_id = self.crear_linia(cursor, uid, factura.id, vals, context=ctx_crear_linia)
                        tax_ids = [x.id for x in line.invoice_line_tax_id]
                        line_obj.write(cursor, uid, line_id, {'invoice_line_tax_id': [(6, 0, tax_ids)]})


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

    @cache()
    def get_rmag_products(self, cursor, uid, context=None):
        """Returns rmag products list"""
        product_obj = self.pool.get('product.product')
        return product_obj.search(cursor, uid, [('default_code', '=', 'RMAG')])

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

    def is_rmag(self, cursor, uid, ids, context=None):
        """Checks invoice line is rmag"""
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        res = dict([(i, False) for i in ids])

        # check if product is rmag
        l_vals = self.read(cursor, uid, ids, ['product_id'], context=context)
        rmag_products = self.get_rmag_products(cursor, uid)

        for l in l_vals:
            if l['product_id'] and l['product_id'][0] in rmag_products:
                res[l['id']] = True
        return res

    def unlink(self, cursor, uid, ids, context=None):
        """Return gkwh rights to owner when gkwh invoice line is droped"""
        if not context:
            context = {}

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
