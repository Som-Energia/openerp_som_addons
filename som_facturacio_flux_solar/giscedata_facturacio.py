# -*- coding: utf-8 -*-
from osv import osv
from osv.expression import OOQuery
from tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta


class GiscedataFacturacioFacturador(osv.osv):
    _name = 'giscedata.facturacio.facturador'
    _inherit = 'giscedata.facturacio.facturador'

    def fact_via_lectures_full_process(self, cursor, uid, fact_ids, context=None):
        if context is None:
            context = {}

        facts = super(GiscedataFacturacioFacturador, self).fact_via_lectures_full_process(cursor, uid, fact_ids,
                                                                                          context=context)
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        extra_obj = self.pool.get('giscedata.facturacio.extra')
        imd_obj = self.pool.get('ir.model.data')
        conf_obj = self.pool.get('res.config')
        product_obj = self.pool.get('product.product')

        descompte_nomes_energia = int(
            conf_obj.get(
                cursor, uid, 'bateria_virtual_descompte_nomes_energia', -1
            )
        )

        uos_id = imd_obj.get_object_reference(
            cursor, uid, 'product', 'product_uom_unit'
        )[1]

        journal_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio',
            'facturacio_journal_energia'
        )[1]

        if descompte_nomes_energia == 1:
            raise osv.except_osv('Error de implementación',
                                 'No se ha implementado la opción de solo descontar la energía')

        product_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio_bateria_virtual",
            "bateria_virtual_product"
        )[1]
        product_brws = product_obj.browse(cursor, uid, product_id, context={'prefetch': False})
        account_id = product_brws.product_tmpl_id.property_account_income.id or product_brws.categ_id.property_account_income_categ.id

        for fact in fact_obj.browse(cursor, uid, facts, context={'prefetch': False}):
            descompte, bat_id, pol_bat_id = self._get_import_bats(cursor, uid, fact.id, context)
            taxes = [x for x in fact.invoice_id.tax_line if x.tax_id.tax_group == 'vat']
            total_base = sum([tax.base_amount for tax in taxes])

            if total_base <= descompte:
                for tax in taxes:
                    vals = {
                        'name': 'Línia de descompte per a la base de {}'.format(tax.tax_id.name),
                        'polissa_id': fact.polissa_id.id,
                        'product_id': product_id,
                        'uos_id': uos_id,
                        'date_from': fact.data_inici,
                        'date_to': fact.data_final,
                        'price_unit': -1 * tax.base_amount * (tax.base_amount / total_base),
                        'quantity': 1,
                        'term': 1,
                        'tipus': 'altres',
                        'account_id': account_id,
                        'tax_ids': [
                            (6, 0, [tax for tax in product_brws.taxes_id])
                        ],
                        'journal_ids': [(6, 0, [journal_id])],
                        'avoid_negative_invoice': True
                    }
                    extra_id = extra_obj.create(cursor, uid, vals, context=context)
                    self.create_discount(cursor, uid, {'data_final': fact.data_final, 'id': fact.id}, bat_id,
                                         extra_id, pol_bat_id, context=context)
            else:
                for tax in taxes:
                    vals = {
                        'name': 'Línia de descompte per a la base de {}'.format(tax.tax_id.name),
                        'polissa_id': fact.polissa_id.id,
                        'product_id': product_id,
                        'uos_id': uos_id,
                        'date_from': fact.data_inici,
                        'date_to': fact.data_final,
                        'price_unit': -1 * tax.base_amount * (tax.base_amount/total_base),
                        'quantity': 1,
                        'term': 1,
                        'tipus': 'altres',
                        'account_id': account_id,
                        'tax_ids': [
                            (6, 0, [tax for tax in product_brws.taxes_id])
                        ],
                        'journal_ids': [(6, 0, [journal_id])],
                        'avoid_negative_invoice': True
                    }
                    extra_id = extra_obj.create(cursor, uid, vals, context=context)
                    self.create_discount(cursor, uid, {'data_final': fact.data_final, 'id': fact.id}, bat_id,
                                         extra_id, pol_bat_id, context=context)

            extra_obj.compute_extra_lines(cursor, uid, [fact.id], context=context)
            fact_obj.button_reset_taxes(cursor, uid, [fact.id], context=context)

        return fact_ids

    def fact_via_lectures_post_invoice_process_pre_compute_iese(self, cursor, uid, fact_ids, context=None):
        return fact_ids

    def _get_import_bats(self, cursor, uid, factura_id, context=None):
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        polissa_bat_obj = self.pool.get("giscedata.bateria.virtual.polissa")

        fact_vals = fact_obj.read(
            cursor, uid, factura_id, [
                'polissa_id', 'data_final', 'data_inici',
                'amount_untaxed', 'number', 'linia_ids'
            ], context=context
        )
        pol_bat_ids = polissa_bat_obj.search(
            cursor, uid, [
                ('polissa_id', '=', fact_vals['polissa_id'][0]),
                ('data_inici', '<=', fact_vals['data_final']),
                ('gestio_descomptes', '!=', 'no_aplicar'),
                '|',
                ('data_final', '>', fact_vals['data_final']),
                ('data_final', '=', False),
            ], context=context
        )

        bat_id = polissa_bat_obj.read(
            cursor, uid, pol_bat_ids[0], ['bateria_id']
        )

        if bat_id:
            bat_id = bat_id['bateria_id']   # (id, 'name')

            return self.descompte_total_import(
                cursor, uid, bat_id[0], pol_bat_ids[0], fact_vals['data_inici'],
                fact_vals['data_final'], context=context
            ), bat_id, pol_bat_ids[0]

        else:
            return 0


GiscedataFacturacioFacturador()