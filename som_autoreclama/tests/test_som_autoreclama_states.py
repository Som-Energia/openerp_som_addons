# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from expects import *
from datetime import date
import mock

from .. import giscedata_atc, som_autoreclama_state_history

class SomAutoreclamaBaseTests(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def search_in(self, model, params):
        model_obj = self.get_model(model)
        found_ids = model_obj.search(self.cursor, self.uid, params)
        return found_ids[0] if found_ids else None

class SomAutoreclamaStatesTest(SomAutoreclamaBaseTests):

    def test_first_state_correct_dummy(self):
        imd_obj = self.get_model('ir.model.data')
        correct_state_id = imd_obj.get_object_reference(
                self.cursor, self.uid, 'som_autoreclama', 'correct_state_workflow_atc'
        )[1]
        sas_obj = self.get_model('som.autoreclama.state')
        first = sas_obj.browse(self.cursor, self.uid, correct_state_id)
        self.assertEqual(first.name, 'Correcte')

    @mock.patch.object(som_autoreclama_state_history.SomAutoreclamaStateHistoryAtc, "create")
    @mock.patch.object(giscedata_atc.GiscedataAtc, "create")
    def test_create_atc__state_correct_in_history(self, mock_create_atc, mock_create_history):
        sash_obj = self.get_model('som.autoreclama.state.history.atc')
        mock_create_atc.return_value = 1

        def create_history_mock(cursor, uid, id, vals):
            return {}

        mock_create_history.side_effect = create_history_mock

        atc_obj = self.get_model('giscedata.atc')
        atc_obj.create(self.cursor, self.uid, {})

        vals = {
            'atc_id': 1,
            'autoreclama_state_id':1,
            'change_date': date.today().strftime("%d-%m-%Y")
        }
        sash_obj.create.assert_called_once_with(self.cursor, self.uid, vals)


class SomAutoreclamaCreationWizardTest(SomAutoreclamaBaseTests):

    """
    def test_create_atc_R1029_from_atc(self):
        atc_obj = self.get_model('giscedata.atc')

        old_atc_id = 1
        new_atc_id = atc_obj.create_related_atc_r1_case_via_wizard(self.cursor, self.uid, old_atc_id, {})

        self.assertEqual(new_atc_id, 2)
        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        # fer un bwose i comprobar coses
    """


    def test_create_general_atc_r1_case_via_wizard__atr_wihtout_r1_type_a(self):
        atc_obj = self.get_model('giscedata.atc')

        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001')[1]

        channel_id = self.search_in('res.partner.canal', [('name','ilike','intercambi')])
        section_id = self.search_in('crm.case.section', [('name','ilike','client')])
        subtipus_id = self.search_in('giscedata.subtipus.reclamacio', [('name','=','029')])

        new_case_data = {
            'polissa_id': polissa_id,
            'descripcio': u'Reclamació per retràs automàtica',
            'canal_id': channel_id,
            'section_id': section_id,
            'subtipus_reclamacio_id': subtipus_id,
            'comentaris': u'test test test',
            'sense_responsable': True,
            'tanca_al_finalitzar_r1': False,
            'crear_cas_r1': False,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(self.cursor, self.uid, new_case_data, {})

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name , new_case_data['descripcio'])
        self.assertEqual(atc.canal_id.id , channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id , subtipus_id)
        self.assertEqual(atc.polissa_id.id , polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1 , new_case_data['tanca_al_finalitzar_r1'])
        self.assertEqual(atc.ref, False )

    def test_create_general_atc_r1_case_via_wizard__atr_wihtout_r1_type_b(self):
        atc_obj = self.get_model('giscedata.atc')

        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002')[1]

        channel_id = self.search_in('res.partner.canal', [('name','ilike','directo')])
        section_id = self.search_in('crm.case.section', [('name','ilike','switching')])
        subtipus_id = self.search_in('giscedata.subtipus.reclamacio', [('name','=','011')])

        new_case_data = {
            'polissa_id': polissa_id,
            'descripcio': u'Reclamació per que si',
            'canal_id': channel_id,
            'section_id': section_id,
            'subtipus_reclamacio_id': subtipus_id,
            'comentaris': u'test test test',
            'sense_responsable': True,
            'tanca_al_finalitzar_r1': False,
            'crear_cas_r1': False,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(self.cursor, self.uid, new_case_data, {})

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name , new_case_data['descripcio'])
        self.assertEqual(atc.canal_id.id , channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id , subtipus_id)
        self.assertEqual(atc.polissa_id.id , polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1 , new_case_data['tanca_al_finalitzar_r1'])
        self.assertEqual(atc.ref, False )

    def test_create_general_atc_r1_case_via_wizard__atr_wihtout_r1_type_c(self):
        atc_obj = self.get_model('giscedata.atc')

        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0003')[1]

        channel_id = self.search_in('res.partner.canal', [('name','ilike','fono')])
        section_id = self.search_in('crm.case.section', [('name','ilike','auto')])
        subtipus_id = self.search_in('giscedata.subtipus.reclamacio', [('name','=','030')])

        new_case_data = {
            'polissa_id': polissa_id,
            'descripcio': u'Reclamació per si de cas',
            'canal_id': channel_id,
            'section_id': section_id,
            'subtipus_reclamacio_id': subtipus_id,
            'comentaris': u'test test test',
            'sense_responsable': True,
            'tanca_al_finalitzar_r1': False,
            'crear_cas_r1': False,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(self.cursor, self.uid, new_case_data, {})

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name , new_case_data['descripcio'])
        self.assertEqual(atc.canal_id.id , channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id , subtipus_id)
        self.assertEqual(atc.polissa_id.id , polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1 , new_case_data['tanca_al_finalitzar_r1'])
        self.assertEqual(atc.ref, False )


    def test_create_general_atc_r1_case_via_wizard__atr_with_r1_type_a(self):
        atc_obj = self.get_model('giscedata.atc')

        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002')[1]

        par_id = self.search_in('res.partner.canal', [('name','ilike','Tiny sprl')])
        par_obj = self.get_model('res.partner')
        par_obj.write(self.cursor, self.uid, par_id, {'ref':'58264'})

        channel_id = self.search_in('res.partner.canal', [('name','ilike','intercambi')])
        section_id = self.search_in('crm.case.section', [('name','ilike','client')])
        subtipus_id = self.search_in('giscedata.subtipus.reclamacio', [('name','=','029')])

        new_case_data = {
            'polissa_id': polissa_id,
            'descripcio': u'Reclamació per retràs automàtica',
            'canal_id': channel_id,
            'section_id': section_id,
            'subtipus_reclamacio_id': subtipus_id,
            'comentaris': u'test test test',
            'sense_responsable': True,
            'tanca_al_finalitzar_r1': True,
            'crear_cas_r1': True,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(self.cursor, self.uid, new_case_data, {})

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name , new_case_data['descripcio'])
        self.assertEqual(atc.canal_id.id , channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id , subtipus_id)
        self.assertEqual(atc.polissa_id.id , polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1 , new_case_data['tanca_al_finalitzar_r1'])

        model, id = atc.ref.split(",")
        self.assertEqual(model, 'giscedata.switching')
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u'R1')
        self.assertEqual(ref.step_id.name, u'01')
        self.assertEqual(ref.section_id.name, u'Switching')
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u'open')


    def test_create_related_atc_r1_case_via_wizard__from_atr(self):
        atc_obj = self.get_model('giscedata.atc')

        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002')[1]

        par_id = self.search_in('res.partner.canal', [('name','ilike','Tiny sprl')])
        par_obj = self.get_model('res.partner')
        par_obj.write(self.cursor, self.uid, par_id, {'ref':'58264'})

        channel_id = self.search_in('res.partner.canal', [('name','ilike','intercambi')])
        section_id = self.search_in('crm.case.section', [('name','ilike','client')])
        subtipus_id = self.search_in('giscedata.subtipus.reclamacio', [('name','=','029')])

        new_case_data = {
            'polissa_id': polissa_id,
            'descripcio': u'Reclamació per retràs automàtica',
            'canal_id': channel_id,
            'section_id': section_id,
            'subtipus_reclamacio_id': subtipus_id,
            'comentaris': u'test test test',
            'sense_responsable': True,
            'tanca_al_finalitzar_r1': True,
            'crear_cas_r1': True,
        }
        old_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(self.cursor, self.uid, new_case_data, {})

        new_atc_id = atc_obj.create_related_atc_r1_case_via_wizard(self.cursor, self.uid, old_atc_id, {})

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.name , new_case_data['descripcio'])
        self.assertEqual(atc.canal_id.id , channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id , subtipus_id)
        self.assertEqual(atc.polissa_id.id , polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1 , new_case_data['tanca_al_finalitzar_r1'])

        model, id = atc.ref.split(",")
        self.assertEqual(model, 'giscedata.switching')
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u'R1')
        self.assertEqual(ref.step_id.name, u'01')
        self.assertEqual(ref.section_id.name, u'Switching')
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u'open')
