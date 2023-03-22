# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import timedelta, date, datetime
from giscedata_switching.tests.common_tests import TestSwitchingImport
from osv import osv, fields

class TestChangeToIndexada(TestSwitchingImport):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def open_polissa(self, xml_id):
        polissa_obj = self.pool.get('giscedata.polissa')
        imd_obj = self.pool.get('ir.model.data')
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', xml_id
        )[1]

        polissa_obj.send_signal(self.cursor, self.uid, [polissa_id], [
            'validar', 'contracte'
        ])

        return polissa_id

    def test_change_to_indexada_inactive_polissa(self):
        imd_obj = self.pool.get('ir.model.data')
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_tarifa_018'
        )[1]
        context = {'active_id': polissa_id}
        wiz_o = self.pool.get('wizard.change.to.indexada')

        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)
        with self.assertRaises(osv.except_osv) as error:
            wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(error.exception.value, u"La pòlissa 0018 no està activa")

    def test_change_to_indexada_modcon_pendent_polissa(self):
        wiz_o = self.pool.get('wizard.change.to.indexada')
        polissa_id = self.open_polissa('polissa_tarifa_018')
        context = {'active_id': polissa_id}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        with self.assertRaises(osv.except_osv) as error:
            wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(error.exception.value, u"La pòlissa 0018 ja té una modificació contractual pendent")

    def test_change_to_indexada_atr_en_curs_polissa(self):
        polissa_obj = self.pool.get('giscedata.polissa')
        wiz_o = self.pool.get('wizard.change.to.indexada')
        polissa_id = self.get_contract_id(self.txn,xml_id="polissa_tarifa_018")
        self.switch(self.txn, 'comer')
        self.change_polissa_comer(self.txn)
        self.update_polissa_distri(self.txn)
        self.activar_polissa_CUPS(self.txn, context=None)
        polissa_obj.send_signal(self.cursor, self.uid, [polissa_id], [
            'validar', 'contracte'
        ])
        context = {'active_id': polissa_id}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)
        step_id = self.create_case_and_step(
            self.cursor, self.uid, polissa_id, 'M1', '01'
        )
        with self.assertRaises(osv.except_osv) as error:
            wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        self.assertEqual(error.exception.value, u"La pòlissa 0018 té casos ATR en curs")

    def test_change_to_indexada_one_polissa(self):
        polissa_obj = self.pool.get('giscedata.polissa')
        modcon_obj = self.pool.get('giscedata.polissa.modcontractual')
        wiz_o = self.pool.get('wizard.change.to.indexada')
        IrModel = self.pool.get('ir.model.data')

        polissa_id = self.open_polissa('polissa_tarifa_018')
        context = {'active_id': polissa_id}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        modcontactual_id = polissa_obj.read(self.cursor, self.uid, polissa_id, ['modcontractuals_ids'])['modcontractuals_ids'][0]
        prev_modcontactual_id = polissa_obj.read(self.cursor, self.uid, polissa_id, ['modcontractuals_ids'])['modcontractuals_ids'][1]


        new_pricelist_id = IrModel._get_obj(self.cursor, self.uid, 'som_indexada', 'pricelist_indexada_peninsula').id

        modcon_act = modcon_obj.read(self.cursor, self.uid, modcontactual_id, [
            'data_inici',
            'data_final',
            'mode_facturacio',
            'mode_facturacio_generacio',
            'llista_preu',
            'coeficient_k',
            'coeficient_d',
            'active',
            'state',
            'modcontractual_ant',
            ])
        modcon_act.pop('id')
        modcon_act['llista_preu'] =  modcon_act['llista_preu'][0]
        modcon_act['modcontractual_ant'] =  modcon_act['modcontractual_ant'][0]

        self.assertEquals(modcon_act,{
            'data_inici': datetime.strftime(date.today() + timedelta(days=1), "%Y-%m-%d"),
            'data_final': datetime.strftime(date.today() + timedelta(days=365), "%Y-%m-%d"),
            'mode_facturacio': 'index',
            'mode_facturacio_generacio': 'index',
            'llista_preu': new_pricelist_id,
            'coeficient_k': 4.82,
            'coeficient_d': 0.3,
            'active': True,
            'state': 'pendent',
            'modcontractual_ant': prev_modcontactual_id,
        })


    def test_change_to_indexada_one_polissa_with_auto(self):
        polissa_obj = self.pool.get('giscedata.polissa')
        modcon_obj = self.pool.get('giscedata.polissa.modcontractual')
        wiz_o = self.pool.get('wizard.change.to.indexada')
        IrModel = self.pool.get('ir.model.data')

        polissa_id = self.open_polissa('polissa_tarifa_018_autoconsum_41')
        context = {'active_id': polissa_id}
        wiz_id = wiz_o.create(self.cursor, self.uid, {}, context=context)

        wiz_o.change_to_indexada(self.cursor, self.uid, [wiz_id], context=context)
        modcontactual_id = polissa_obj.read(self.cursor, self.uid, polissa_id, ['modcontractuals_ids'])['modcontractuals_ids'][0]
        prev_modcontactual_id = polissa_obj.read(self.cursor, self.uid, polissa_id, ['modcontractuals_ids'])['modcontractuals_ids'][1]


        new_pricelist_id = IrModel._get_obj(self.cursor, self.uid, 'som_indexada', 'pricelist_indexada_peninsula').id

        modcon_act = modcon_obj.read(self.cursor, self.uid, modcontactual_id, [
            'data_inici',
            'data_final',
            'mode_facturacio',
            'mode_facturacio_generacio',
            'llista_preu',
            'coeficient_k',
            'coeficient_d',
            'active',
            'state',
            'modcontractual_ant',
            'autoconsumo',
            ])
        modcon_act.pop('id')
        modcon_act['llista_preu'] =  modcon_act['llista_preu'][0]
        modcon_act['modcontractual_ant'] =  modcon_act['modcontractual_ant'][0]

        self.assertEquals(modcon_act,{
            'data_inici': datetime.strftime(date.today() + timedelta(days=1), "%Y-%m-%d"),
            'data_final': datetime.strftime(date.today() + timedelta(days=365), "%Y-%m-%d"),
            'mode_facturacio': 'index',
            'mode_facturacio_generacio': 'index',
            'llista_preu': new_pricelist_id,
            'coeficient_k': 4.82,
            'coeficient_d': 0.3,
            'active': True,
            'state': 'pendent',
            'modcontractual_ant': prev_modcontactual_id,
            'autoconsumo': '41',
        })
