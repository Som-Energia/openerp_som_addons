# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import timedelta, datetime
from osv import osv

class TestWizardGestioTextToPolissa(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestWizardGestioTextToPolissa, self).setUp()
        self.pool = self.openerp.pool


    def test_get_polissa_ids_from_f1_pol_activa(self):
        imd_obj = self.pool.get('ir.model.data')
        wiz_o = self.pool.get('wizard.gestio.text.to.polissa')
        f1_o = self.pool.get("giscedata.facturacio.importacio.linia")
        pol_o = self.pool.get("giscedata.polissa")

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_0001"
        )[1]
        pol_o.write(self.cursor, self.uid, pol_id, {'state':'activa'})
        pol = pol_o.browse(self.cursor, self.uid, pol_id)

        other_pols_id = pol_o.search(self.cursor, self.uid, [('cups', '=', pol.cups.id), ('state','!=', 'activa')])
        pol_o.write(self.cursor, self.uid, other_pols_id, {'cups': False})

        f1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_01_f1_import_01"
        )[1]
        fecha_factura_desde = pol.data_alta
        fecha_factura_hasta = datetime.strptime(fecha_factura_desde, '%Y-%m-%d') + timedelta(days=15)
        fecha_factura_hasta = fecha_factura_hasta.strftime("%Y-%m-%d")
        f1_o.write(self.cursor, self.uid, f1_id, {
            'cups_id': pol.cups.id, 'fecha_factura_desde': fecha_factura_desde, 'fecha_factura_hasta': fecha_factura_hasta,
            'cups_text': pol.cups.name})


        wiz_init = {'field_to_write': 'info_gestio_endarrerida'}
        context = {'active_ids': [f1_id], 'from_model': 'giscedata.facturacio.importacio.linia'}
        wiz_id = wiz_o.create(self.cursor, self.uid, wiz_init, context=context)

        result = wiz_o.get_polisses_ids(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(result, [pol.id])


    def test_get_polissa_ids_from_f1_pol_activa_different_cups(self):
        imd_obj = self.pool.get('ir.model.data')
        wiz_o = self.pool.get('wizard.gestio.text.to.polissa')
        f1_o = self.pool.get("giscedata.facturacio.importacio.linia")
        pol_o = self.pool.get("giscedata.polissa")

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_0001"
        )[1]
        pol_o.write(self.cursor, self.uid, pol_id, {'state':'activa'})
        pol = pol_o.browse(self.cursor, self.uid, pol_id)

        other_pols_id = pol_o.search(self.cursor, self.uid, [('cups', '=', pol.cups.id), ('state','!=', 'activa')])
        pol_o.write(self.cursor, self.uid, other_pols_id, {'cups': False})

        f1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_01_f1_import_01"
        )[1]
        fecha_factura_desde = pol.data_alta
        fecha_factura_hasta = datetime.strptime(fecha_factura_desde, '%Y-%m-%d') + timedelta(days=15)
        fecha_factura_hasta = fecha_factura_hasta.strftime("%Y-%m-%d")
        f1_o.write(self.cursor, self.uid, f1_id, {
            'cups_id': pol.cups.id, 'fecha_factura_desde': fecha_factura_desde, 'fecha_factura_hasta': fecha_factura_hasta,
            'cups_text': pol.cups.name[:20] + 'TT'})


        wiz_init = {'field_to_write': 'info_gestio_endarrerida'}
        context = {'active_ids': [f1_id], 'from_model': 'giscedata.facturacio.importacio.linia'}
        wiz_id = wiz_o.create(self.cursor, self.uid, wiz_init, context=context)

        result = wiz_o.get_polisses_ids(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(result, [pol.id])

    def test_get_polissa_ids_from_f1_pol_baixa(self):
        imd_obj = self.pool.get('ir.model.data')
        wiz_o = self.pool.get('wizard.gestio.text.to.polissa')
        f1_o = self.pool.get("giscedata.facturacio.importacio.linia")
        pol_o = self.pool.get("giscedata.polissa")

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_0001"
        )[1]
        pol_o.write(self.cursor, self.uid, pol_id, {'state':'baixa', 'active': False})
        pol = pol_o.browse(self.cursor, self.uid, pol_id)

        other_pols_id = pol_o.search(self.cursor, self.uid, [('cups', '=', pol.cups.id), ('state','!=', 'activa')])
        pol_o.write(self.cursor, self.uid, other_pols_id, {'cups': False})

        f1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_01_f1_import_01"
        )[1]
        fecha_factura_desde = pol.data_alta
        fecha_factura_hasta = datetime.strptime(fecha_factura_desde, '%Y-%m-%d') + timedelta(days=15)
        fecha_factura_hasta = fecha_factura_hasta.strftime("%Y-%m-%d")
        f1_o.write(self.cursor, self.uid, f1_id, {
            'cups_id': pol.cups.id, 'fecha_factura_desde': fecha_factura_desde, 'fecha_factura_hasta': fecha_factura_hasta,
            'cups_text': pol.cups.name})

        wiz_init = {'field_to_write': 'info_gestio_endarrerida'}
        context = {'active_ids': [f1_id], 'from_model': 'giscedata.facturacio.importacio.linia'}
        wiz_id = wiz_o.create(self.cursor, self.uid, wiz_init, context=context)

        result = wiz_o.get_polisses_ids(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(result, [pol.id])


    def test_get_polissa_ids_from_f1__single(self):
        imd_obj = self.pool.get('ir.model.data')
        pol_obj = self.pool.get('giscedata.polissa')
        cups_obj = self.pool.get('giscedata.cups.ps')
        wiz_o = self.pool.get('wizard.gestio.text.to.polissa')
        line_obj = self.openerp.pool.get('giscedata.facturacio.importacio.linia')
        lid = line_obj.search(self.cursor, self.uid, [])[0]

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_0001"
        )[1]

        pol_vals = {'lot_facturacio': False,
                    'data_baixa': False,
                    'data_alta': '2021-01-01'}
        pol_obj.write(self.cursor, self.uid, pol_id, pol_vals)

        cups_data = cups_obj.browse(self.cursor, self.uid, pol_id)
        vals = { 'cups_id': cups_data.id,
                 'cups_text': cups_data.name,
                 'fecha_factura_desde': '2021-06-01',
                 'fecha_factura_hasta': '2021-07-01',
                 }
        line_obj.write(self.cursor, self.uid, lid, vals)

        wiz_init = {'field_to_write': 'info_gestio_endarrerida'}
        context = {'active_ids': [lid], 'from_model': 'giscedata.facturacio.importacio.linia'}
        wiz_id = wiz_o.create(self.cursor, self.uid, wiz_init, context=context)

        result = wiz_o.get_polisses_ids(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(result, [lid])

    def test_get_polissa_ids_from_f1__many(self):
        imd_obj = self.pool.get('ir.model.data')
        pol_obj = self.pool.get('giscedata.polissa')
        cups_obj = self.pool.get('giscedata.cups.ps')
        wiz_o = self.pool.get('wizard.gestio.text.to.polissa')
        line_obj = self.openerp.pool.get('giscedata.facturacio.importacio.linia')
        lid1 = line_obj.search(self.cursor, self.uid, [])[0]
        lid2 = line_obj.search(self.cursor, self.uid, [])[1]

        pol1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_0001"
        )[1]
        pol2_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_0002"
        )[1]

        pol_vals = {'lot_facturacio': False,
                    'data_baixa': False,
                    'data_alta': '2021-01-01'}
        pol_obj.write(self.cursor, self.uid, [pol1_id, pol2_id], pol_vals)

        cups1_data = cups_obj.browse(self.cursor, self.uid, pol1_id)
        cups2_data = cups_obj.browse(self.cursor, self.uid, pol2_id)

        vals1 = {'cups_id': cups1_data.id,
                'cups_text': cups1_data.name,
                'fecha_factura_desde': '2021-06-01',
                'fecha_factura_hasta': '2021-07-01',
                }
        vals2 = {'cups_id': cups2_data.id,
                'cups_text': cups2_data.name,
                'fecha_factura_desde': '2021-07-01',
                'fecha_factura_hasta': '2021-08-01',
                }
        line_obj.write(self.cursor, self.uid, lid1, vals1)
        line_obj.write(self.cursor, self.uid, lid2, vals2)

        wiz_init = {'field_to_write': 'info_gestio_endarrerida'}
        context = {'active_ids': [lid1, lid2], 'from_model': 'giscedata.facturacio.importacio.linia'}
        wiz_id = wiz_o.create(self.cursor, self.uid, wiz_init, context=context)

        result = wiz_o.get_polisses_ids(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(result, [lid1, lid2])


    def test_get_polissa_ids_from_f1__out_of_f1_date_range(self):
        imd_obj = self.pool.get('ir.model.data')
        pol_obj = self.pool.get('giscedata.polissa')
        cups_obj = self.pool.get('giscedata.cups.ps')
        wiz_o = self.pool.get('wizard.gestio.text.to.polissa')
        line_obj = self.openerp.pool.get('giscedata.facturacio.importacio.linia')
        lid = line_obj.search(self.cursor, self.uid, [])[0]

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', "polissa_0001"
        )[1]

        pol_vals = {'lot_facturacio': False,
                    'data_baixa': '2021-05-30',
                    'data_alta': '2021-01-01'}
        pol_obj.write(self.cursor, self.uid, pol_id, pol_vals)

        cups_data = cups_obj.browse(self.cursor, self.uid, pol_id)
        vals = {'cups_id': cups_data.id,
                'cups_text': cups_data.name,
                'fecha_factura_desde': '2021-06-01',
                'fecha_factura_hasta': '2021-07-01',
                }
        line_obj.write(self.cursor, self.uid, lid, vals)

        wiz_init = {'field_to_write': 'info_gestio_endarrerida'}
        context = {'active_ids': [lid], 'from_model': 'giscedata.facturacio.importacio.linia'}
        wiz_id = wiz_o.create(self.cursor, self.uid, wiz_init, context=context)

        with self.assertRaises(osv.except_osv) as exception_context:
            result = wiz_o.get_polisses_ids(self.cursor, self.uid, [wiz_id], context=context)

        expected_message = 'No s\'ha trobat pòlissa per l\'F1 amb cups {}'.format(cups_data.name)
        exception_message = exception_context.exception.message

        self.assertIn(expected_message, exception_message)
