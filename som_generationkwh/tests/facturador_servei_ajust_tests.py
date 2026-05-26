# -*- coding: utf-8 -*-
from datetime import date, timedelta

from destral import testing


class FacturadorServeiAjustTests(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(FacturadorServeiAjustTests, self).setUp()
        self.pool = self.openerp.pool
        self.facturador = self.pool.get('giscedata.facturacio.facturador')
        self.factura_obj = self.pool.get('giscedata.facturacio.factura')
        self.line_obj = self.pool.get('giscedata.facturacio.factura.linia')
        self.polissa_obj = self.pool.get('giscedata.polissa')
        self.pl_obj = self.pool.get('product.pricelist')
        self.imd_obj = self.pool.get('ir.model.data')

        self.factura_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio', 'factura_0001'
        )[1]

    def _prepare_factura(self):
        factura = self.factura_obj.browse(self.cursor, self.uid, self.factura_id)
        self.polissa_obj.write(
            self.cursor, self.uid, [factura.polissa_id.id], {'te_assignacio_gkwh': True}
        )
        existing_gkwh_ids = self.factura_obj.get_gkwh_lines(
            self.cursor, self.uid, self.factura_id, context={})
        if existing_gkwh_ids:
            self.line_obj.unlink(self.cursor, self.uid, existing_gkwh_ids,
                                 context={'gkwh_manage_rights': False})

    def _set_mode_facturacio(self, mode):
        factura = self.factura_obj.browse(self.cursor, self.uid, self.factura_id)
        self.polissa_obj.write(
            self.cursor, self.uid, [factura.polissa_id.id], {'mode_facturacio': mode}
        )

    def _create_modcon(self, data_inici, data_final, mode, polissa_id=None):
        factura = self.factura_obj.browse(self.cursor, self.uid, self.factura_id)
        target_polissa_id = polissa_id or factura.polissa_id.id
        self.polissa_obj.write(
            self.cursor,
            self.uid,
            target_polissa_id,
            {
                'mode_facturacio': mode,
                'mode_facturacio_generacio': mode,
            }
        )
        polissa = self.polissa_obj.browse(self.cursor, self.uid, target_polissa_id)
        polissa.send_signal(['modcontractual'])

        wizard_obj = self.pool.get('giscedata.polissa.crear.contracte')
        ctx = {'active_id': target_polissa_id}
        wizard_id = wizard_obj.create(self.cursor, self.uid, {'duracio': 'nou'}, ctx)
        wizard = wizard_obj.browse(self.cursor, self.uid, wizard_id, ctx)
        wizard_obj.onchange_duracio(
            self.cursor, self.uid, [wizard_id], wizard.data_inici, wizard.duracio, ctx
        )
        wizard.write({'data_inici': data_inici, 'data_final': data_final})
        wizard.action_crear_contracte(ctx)

    def _get_template_energy_line(self):
        factura = self.factura_obj.browse(self.cursor, self.uid, self.factura_id)
        for line in factura.linia_ids:
            if line.tipus == 'energia':
                return line
        raise AssertionError('No energy line found in demo invoice')

    def _create_saju_line(self, quantity, force_price=0.5, name='SAJU test'):
        template = self._get_template_energy_line()
        saju_product_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_repercussio_servei_ajust', 'servei_ajust'
        )[1]
        vals = {
            'factura_id': self.factura_id,
            'data_desde': template.data_desde,
            'data_fins': template.data_fins,
            'uos_id': template.uos_id.id,
            'quantity': quantity,
            'product_id': saju_product_id,
            'tipus': 'energia',
            'name': name,
            'force_price': force_price,
            'multi': 1,
            'account_id': template.account_id.id,
            'invoice_line_tax_id': [(6, 0, [t.id for t in template.invoice_line_tax_id])],
            'uom_multi_id': template.uom_multi_id and template.uom_multi_id.id or False,
        }
        return self.line_obj.create(self.cursor, self.uid, vals, context={'group_line': False})

    def _create_gkwh_line(self, quantity, data_desde=None, data_fins=None):
        template = self._get_template_energy_line()
        gkwh_products = self.line_obj.get_gkwh_products(self.cursor, self.uid)
        if not gkwh_products:
            raise AssertionError('No GKWH products found')
        vals = {
            'factura_id': self.factura_id,
            'data_desde': data_desde or template.data_desde,
            'data_fins': data_fins or template.data_fins,
            'uos_id': template.uos_id.id,
            'quantity': quantity,
            'product_id': gkwh_products[0],
            'tipus': 'energia',
            'name': 'GKWH test',
            'force_price': 0.0,
            'multi': 1,
            'account_id': template.account_id.id,
            'invoice_line_tax_id': [(6, 0, [t.id for t in template.invoice_line_tax_id])],
            'uom_multi_id': template.uom_multi_id and template.uom_multi_id.id or False,
        }
        return self.line_obj.create(self.cursor, self.uid, vals, context={'group_line': False})

    def test_reconcile_saju_indexada_with_gkwh_updates_line(self):
        self._prepare_factura()
        self._set_mode_facturacio('index')
        saju_line_id = self._create_saju_line(quantity=20.0, force_price=0.5)
        self._create_gkwh_line(quantity=4.0, data_desde='2026-05-01', data_fins='2026-05-31')
        self._create_gkwh_line(quantity=6.0, data_desde='2026-06-01', data_fins='2026-06-30')

        self.facturador.reconcile_servei_ajust_generationkwh(
            self.cursor, self.uid, [self.factura_id], context={}
        )

        saju_line = self.line_obj.browse(self.cursor, self.uid, saju_line_id)
        self.assertEqual(saju_line.quantity, 10.0)
        self.assertIn('(Generation kWh)', saju_line.name)

    def test_reconcile_saju_indexada_without_gkwh_deletes_line(self):
        self._prepare_factura()
        self._set_mode_facturacio('index')
        saju_line_id = self._create_saju_line(quantity=20.0, force_price=0.5)

        self.facturador.reconcile_servei_ajust_generationkwh(
            self.cursor, self.uid, [self.factura_id], context={}
        )

        still_exists = self.line_obj.search(self.cursor, self.uid, [('id', '=', saju_line_id)])
        self.assertEqual(still_exists, [])

    def test_reconcile_saju_not_indexada_with_gkwh_keeps_line(self):
        self._prepare_factura()
        self._set_mode_facturacio('atr')
        saju_line_id = self._create_saju_line(quantity=20.0, force_price=0.5)
        self._create_gkwh_line(quantity=6.0, data_desde='2026-05-01', data_fins='2026-05-31')

        self.facturador.reconcile_servei_ajust_generationkwh(
            self.cursor, self.uid, [self.factura_id], context={}
        )

        saju_line = self.line_obj.browse(self.cursor, self.uid, saju_line_id)
        self.assertEqual(saju_line.quantity, 20.0)

    def test_reconcile_saju_with_zero_saju_quantity_does_not_change_line(self):
        self._prepare_factura()
        self._set_mode_facturacio('index')
        saju_line_id = self._create_saju_line(quantity=0.0, force_price=0.5, name='SAJU original')
        self._create_gkwh_line(quantity=2.0, data_desde='2026-05-01', data_fins='2026-05-31')

        self.facturador.reconcile_servei_ajust_generationkwh(
            self.cursor, self.uid, [self.factura_id], context={}
        )

        saju_line = self.line_obj.browse(self.cursor, self.uid, saju_line_id)
        self.assertEqual(saju_line.quantity, 0.0)
        self.assertEqual(saju_line.name, 'SAJU original')

    def test_reconcile_uses_mode_facturacio_at_invoice_date(self):
        self._prepare_factura()
        today = date.today()
        yesterday = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        tomorrow = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        future_end = (today + timedelta(days=365)).strftime('%Y-%m-%d')
        test_polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_tarifa_018'
        )[1]

        self.polissa_obj.send_signal(self.cursor, self.uid, [
                                     test_polissa_id], ['validar', 'contracte'])
        self.factura_obj.write(
            self.cursor,
            self.uid,
            [self.factura_id],
            {'polissa_id': test_polissa_id}
        )

        self._set_mode_facturacio('atr')
        self._create_modcon(yesterday, yesterday, 'index', polissa_id=test_polissa_id)
        self._create_modcon(tomorrow, future_end, 'atr', polissa_id=test_polissa_id)
        saju_line_id = self._create_saju_line(quantity=20.0, force_price=0.5)
        self.factura_obj.write(
            self.cursor,
            self.uid,
            [self.factura_id],
            {
                'data_inici': yesterday,
                'data_final': yesterday,
            }
        )

        self.facturador.reconcile_servei_ajust_generationkwh(
            self.cursor, self.uid, [self.factura_id], context={}
        )

        still_exists = self.line_obj.search(self.cursor, self.uid, [('id', '=', saju_line_id)])
        self.assertEqual(still_exists, [])

    def test_reconcile_ignores_gkwh_lines_before_2026_05_01(self):
        self._prepare_factura()
        self._set_mode_facturacio('index')
        saju_line_id = self._create_saju_line(quantity=20.0, force_price=0.5)
        self._create_gkwh_line(quantity=8.0, data_desde='2026-04-01', data_fins='2026-04-30')
        self._create_gkwh_line(quantity=3.0, data_desde='2026-05-01', data_fins='2026-05-31')

        self.facturador.reconcile_servei_ajust_generationkwh(
            self.cursor, self.uid, [self.factura_id], context={}
        )

        saju_line = self.line_obj.browse(self.cursor, self.uid, saju_line_id)
        self.assertEqual(saju_line.quantity, 3.0)
        self.assertIn('(Generation kWh)', saju_line.name)
