# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import timedelta, datetime
from osv import osv
import mock

class TestWizardDeleteReimport2001f1(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(TestWizardDeleteReimport2001f1, self).setUp()
        self.pool = self.openerp.pool


    def test_delete_reimport_valid_f1(self):
        imd_obj = self.pool.get('ir.model.data')
        wiz_o = self.pool.get('wizard.delete.reimport.2001.f1')
        f1_o = self.pool.get("giscedata.facturacio.importacio.linia")

        f1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_01_f1_import_01"
        )[1]
        f1_o.write(self.cursor, self.uid, f1_id, {'state':'valid', 'invoice_number_text':'282302'})

        context = {'active_ids': [f1_id]}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        result = wiz_o.delete_reimport(self.cursor, self.uid, [wiz_id], context=context)
        info = wiz_o.browse(self.cursor, self.uid, wiz_id).info
        self.assertEqual(info, "Errors:\nF1 amb origen 282302 no és erroni\n\n")

    def test_delete_reimport_correct_second_f1(self):
        imd_obj = self.pool.get('ir.model.data')
        wiz_o = self.pool.get('wizard.delete.reimport.2001.f1')
        f1_o = self.pool.get("giscedata.facturacio.importacio.linia")
        f1_error_o = self.pool.get("giscedata.facturacio.switching.error")

        f1_error_id = f1_error_o.create(self.cursor, self.uid, {'name':'2001', 'message':'Error 2001'})

        f1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_01_f1_import_01"
        )[1]
        f1_o.write(self.cursor, self.uid, f1_id,
            {'state':'erroni', 'invoice_number_text':'282302', 'lectures_processades':False, 'error_ids':[(6,0, [f1_error_id])]}
        )
        f1 = f1_o.browse(self.cursor, self.uid, f1_id)

        f1_id_2 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_02_f1_import_01"
        )[1]
        f1_o.write(self.cursor, self.uid, f1_id_2,
            {'state':'erroni', 'invoice_number_text':'282302', 'state': 'valid', 'distribuidora_id':f1.distribuidora_id.id}
        )
        context = {'active_ids': [f1_id]}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        result = wiz_o.delete_reimport(self.cursor, self.uid, [wiz_id], context=context)
        info = wiz_o.browse(self.cursor, self.uid, wiz_id).info
        self.assertEqual(info,
            "Errors:\nPer l'origen 282302 hi ha un F1 correcte sense warning 2002, ID: {}\n"
            "Per l'origen 282302 es podrien esborrar els F1 ns []\n\n".format(f1_id_2)
            )

    def test_delete_reimport_correct_and_error_f1(self):
        imd_obj = self.pool.get('ir.model.data')
        wiz_o = self.pool.get('wizard.delete.reimport.2001.f1')
        f1_o = self.pool.get("giscedata.facturacio.importacio.linia")
        f1_error_o = self.pool.get("giscedata.facturacio.switching.error")

        f1_error_id = f1_error_o.create(self.cursor, self.uid, {'name':'2001', 'message':'Error 2001'})
        f1_error_id_3 = f1_error_o.create(self.cursor, self.uid, {'name':'2001', 'message':'Error 2001'})

        f1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_01_f1_import_01"
        )[1]
        f1_o.write(self.cursor, self.uid, f1_id,
            {'state':'erroni', 'invoice_number_text':'282302', 'lectures_processades':False, 'error_ids':[(6,0, [f1_error_id])]}
        )
        f1 = f1_o.browse(self.cursor, self.uid, f1_id)

        f1_id_2 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_02_f1_import_01"
        )[1]
        f1_o.write(self.cursor, self.uid, f1_id_2,
            {'state':'erroni', 'invoice_number_text':'282302', 'state': 'valid', 'distribuidora_id':f1.distribuidora_id.id}
        )
        f1_id_3 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_03_f1_import_01"
        )[1]
        f1_o.write(self.cursor, self.uid, f1_id_3,
            {'state':'erroni', 'invoice_number_text':'282302', 'lectures_processades':False,
            'distribuidora_id':f1.distribuidora_id.id, 'error_ids':[(6,0, [f1_error_id_3])]}
        )
        pre_f1_ids = f1_o.search(self.cursor, self.uid,
            [('invoice_number_text','=',f1.invoice_number_text),('distribuidora_id','=',f1.distribuidora_id.id)]
        )
        self.assertEqual(len(pre_f1_ids), 3)

        context = {'active_ids': [f1_id]}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        result = wiz_o.delete_reimport(self.cursor, self.uid, [wiz_id], context=context)
        info = wiz_o.browse(self.cursor, self.uid, wiz_id).info
        self.assertEqual(info,
            "Errors:\nPer l'origen 282302 hi ha un F1 correcte sense warning 2002, ID: {}\n"
            "Per l'origen 282302 es podrien esborrar els F1 ns [{}L]\n\n".format(f1_id_2, f1_id_3)
            )


    def test_delete_reimport_not_2001_error(self):
        imd_obj = self.pool.get('ir.model.data')
        wiz_o = self.pool.get('wizard.delete.reimport.2001.f1')
        f1_o = self.pool.get("giscedata.facturacio.importacio.linia")

        f1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_01_f1_import_01"
        )[1]
        f1_o.write(self.cursor, self.uid, f1_id, {'state':'erroni', 'invoice_number_text':'282302', 'lectures_processades':False})

        context = {'active_ids': [f1_id]}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        result = wiz_o.delete_reimport(self.cursor, self.uid, [wiz_id], context=context)
        info = wiz_o.browse(self.cursor, self.uid, wiz_id).info
        self.assertEqual(info, "Errors:\nF1 amb origen 282302 no té error 2001\n\n")


    def test_delete_reimport_open_invoice(self):
        imd_obj = self.pool.get('ir.model.data')
        wiz_o = self.pool.get('wizard.delete.reimport.2001.f1')
        f1_o = self.pool.get("giscedata.facturacio.importacio.linia")
        fact_o = self.pool.get("giscedata.facturacio.factura")
        f1_error_o = self.pool.get("giscedata.facturacio.switching.error")

        f1_error_id = f1_error_o.create(self.cursor, self.uid, {'name':'2001', 'message':'Error 2001'})

        f1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_01_f1_import_01"
        )[1]
        f1_o.write(self.cursor, self.uid, f1_id,
            {'state':'erroni', 'invoice_number_text':'282302', 'lectures_processades':False, 'error_ids':[(6,0, [f1_error_id])]}
        )
        f1 = f1_o.browse(self.cursor, self.uid, f1_id)

        fact_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio', "factura_dso_0002"
        )[1]
        fact_o.write(self.cursor, self.uid, fact_id,
            {'state':'open', 'origin':f1.invoice_number_text, 'partner_id':f1.distribuidora_id.id},
            context={'skip_cnt_llista_preu_compatible':True}
        )

        context = {'active_ids': [f1_id]}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        result = wiz_o.delete_reimport(self.cursor, self.uid, [wiz_id], context=context)
        info = wiz_o.browse(self.cursor, self.uid, wiz_id).info
        self.assertEqual(info, "Errors:\nF1 amb origen 282302 té una factura de proveïdor no en esborrany\n\n")

    @mock.patch("giscedata_facturacio_switching.wizard.giscedata_facturacio_switching_wizard.GiscedataFacturacioSwitchingWizard.sub_action_importar_f1")
    def test_delete_reimport_delete(self, mocked):
        imd_obj = self.pool.get('ir.model.data')
        wiz_o = self.pool.get('wizard.delete.reimport.2001.f1')
        f1_o = self.pool.get("giscedata.facturacio.importacio.linia")
        fact_o = self.pool.get("giscedata.facturacio.factura")
        f1_error_o = self.pool.get("giscedata.facturacio.switching.error")

        f1_error_id = f1_error_o.create(self.cursor, self.uid, {'name':'2001', 'message':'Error 2001'})

        f1_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_01_f1_import_01"
        )[1]
        f1_o.write(self.cursor, self.uid, f1_id,
            {'state':'erroni', 'invoice_number_text':'282302', 'lectures_processades':False, 'error_ids':[(6,0, [f1_error_id])]}
        )
        f1 = f1_o.browse(self.cursor, self.uid, f1_id)

        f1_id_2 = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio_switching', "line_02_f1_import_01"
        )[1]
        f1_o.write(self.cursor, self.uid, f1_id_2,
            {'state':'erroni', 'invoice_number_text':'282302', 'lectures_processades':False, 'distribuidora_id':f1.distribuidora_id.id}
        )

        pre_f1_ids = f1_o.search(self.cursor, self.uid,
            [('invoice_number_text','=',f1.invoice_number_text),('distribuidora_id','=',f1.distribuidora_id.id)]
        )
        self.assertEqual(len(pre_f1_ids), 2)

        context = {'active_ids': [f1_id]}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        result = wiz_o.delete_reimport(self.cursor, self.uid, [wiz_id], context=context)

        post_f1_ids = f1_o.search(self.cursor, self.uid,
            [('invoice_number_text','=',f1.invoice_number_text),('distribuidora_id','=',f1.distribuidora_id.id)]
        )
        self.assertEqual(post_f1_ids, [f1_id])

        ctx = {'active_ids': [f1_id], 'active_id': f1_id}
        mocked.assert_called_with(self.cursor, self.uid, mock.ANY, context=ctx)

        info = wiz_o.browse(self.cursor, self.uid, wiz_id).info
        self.assertEqual(info, "Errors:\n\n\n" + "S'estan reimportant en segon pla els següents F1:\n{}\n\n".format([f1_id]))

        f1 = f1_o.browse(self.cursor, self.uid, f1_id)

        self.assertEqual(
            u"Reimportat mitjançant l'acció de \"(2001) Eliminar F1 mateix origen i reimportar\"\n",
            f1.user_observations
        )
