# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from expects import *
from datetime import date, timedelta
import mock

from .. import giscedata_atc, som_autoreclama_state_history

def today_str():
    return date.today().strftime("%Y-%m-%d")

def today_minus_str(d):
    return (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")


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

    def browse_referenced(self, reference):
        model, id = reference.split(',')
        model_obj = self.get_model(model)
        return model_obj.browse(self.cursor, self.uid, int(id))


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
    def _test_create_atc__state_correct_in_history(self, mock_create_atc, mock_create_history):
        sash_obj = self.get_model('som.autoreclama.state.history.atc')
        mock_create_atc.return_value = 1

        def create_history_mock(cursor, uid, id, vals):
            return {}

        mock_create_history.side_effect = create_history_mock

        atc_obj = self.get_model('giscedata.atc')
        atc_obj.create(self.cursor, self.uid, {})

        vals = {
            'atc_id': 1,
            'state_id':1,
            'change_date': today_str()
        }
        sash_obj.create.assert_called_once_with(self.cursor, self.uid, vals)

    def test_create_atc__first_state_correct_in_history_indirectly(self):
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

        self.assertEqual(atc.autoreclama_state.name, 'Correcte')
        self.assertEqual(atc.autoreclama_state_date, today_str())
        self.assertEqual(len(atc.autoreclama_history_ids), 1)

    def test_create_atc__first_state_correct_in_history_indirectly_a(self):
        atc_obj = self.get_model('giscedata.atc')

        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001')[1]

        channel_id = self.search_in('res.partner.canal', [('name','ilike','intercambi')])
        section_id = self.search_in('crm.case.section', [('name','ilike','client')])
        subtipus_id = self.search_in('giscedata.subtipus.reclamacio', [('name','=','029')])

        state_0_id = self.search_in('som.autoreclama.state', [('name','ilike','correc')])
        state_0_dt = '2022-01-02'

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
        ctxt = {
            'autoreclama_history_initial_state_id':state_0_id,
            'autoreclama_history_initial_date': state_0_dt,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(self.cursor, self.uid, new_case_data, ctxt)

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.autoreclama_state.id, state_0_id)
        self.assertEqual(atc.autoreclama_state_date, state_0_dt)
        self.assertEqual(len(atc.autoreclama_history_ids), 1)

    def test_historize__second_state_correct_in_history_indirectly(self):
        atc_obj = self.get_model('giscedata.atc')
        history_obj = self.get_model('som.autoreclama.state.history.atc')

        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001')[1]

        channel_id = self.search_in('res.partner.canal', [('name','ilike','intercambi')])
        section_id = self.search_in('crm.case.section', [('name','ilike','client')])
        subtipus_id = self.search_in('giscedata.subtipus.reclamacio', [('name','=','029')])

        state_0_id = self.search_in('som.autoreclama.state', [('name','ilike','correc')])
        state_0_dt = '2022-01-02'
        state_1_id = self.search_in('som.autoreclama.state', [('name','ilike','desact')])
        state_1_dt = '2022-02-15'
        state_1_st = 2

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
        ctxt = {
            'autoreclama_history_initial_state_id':state_0_id,
            'autoreclama_history_initial_date': state_0_dt,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(self.cursor, self.uid, new_case_data, ctxt)
        state_1_st = new_atc_id
        history_obj.historize(self.cursor, self.uid, new_atc_id, state_1_id, state_1_dt, state_1_st)

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.autoreclama_state.id, state_1_id )
        self.assertEqual(atc.autoreclama_state_date, state_1_dt )
        self.assertEqual(len(atc.autoreclama_history_ids), 2)

        self.assertEqual(atc.autoreclama_history_ids[1].state_id.id, state_0_id )
        self.assertEqual(atc.autoreclama_history_ids[1].change_date, state_0_dt )
        self.assertEqual(atc.autoreclama_history_ids[1].end_date, state_1_dt )
        self.assertEqual(atc.autoreclama_history_ids[1].atc_id.id, new_atc_id )
        self.assertEqual(atc.autoreclama_history_ids[1].generated_atc_id.id, False )

    def test_historize__third_state_correct_in_history_indirectly(self):
        atc_obj = self.get_model('giscedata.atc')
        history_obj = self.get_model('som.autoreclama.state.history.atc')

        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001')[1]

        channel_id = self.search_in('res.partner.canal', [('name','ilike','intercambi')])
        section_id = self.search_in('crm.case.section', [('name','ilike','client')])
        subtipus_id = self.search_in('giscedata.subtipus.reclamacio', [('name','=','029')])
        state_0_id = self.search_in('som.autoreclama.state', [('name','ilike','correc')])
        state_0_dt = '2022-01-02'
        state_1_id = self.search_in('som.autoreclama.state', [('name','ilike','reclam')])
        state_1_dt = '2022-02-15'
        state_1_st = 3
        state_2_id = self.search_in('som.autoreclama.state', [('name','ilike','desact')])
        state_2_dt = '2022-04-16'
        state_2_st = 4

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
        ctxt = {
            'autoreclama_history_initial_state_id':state_0_id,
            'autoreclama_history_initial_date': state_0_dt,
        }
        new_atc_id = atc_obj.create_general_atc_r1_case_via_wizard(self.cursor, self.uid, new_case_data, ctxt)

        state_1_st = state_2_st = new_atc_id
        history_obj.historize(self.cursor, self.uid, new_atc_id, state_1_id, state_1_dt, state_1_st)
        history_obj.historize(self.cursor, self.uid, new_atc_id, state_2_id, state_2_dt, state_2_st)

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)

        self.assertEqual(atc.autoreclama_state.id, state_2_id )
        self.assertEqual(atc.autoreclama_state_date, state_2_dt )
        self.assertEqual(len(atc.autoreclama_history_ids), 3)

        self.assertEqual(atc.autoreclama_history_ids[1].state_id.id, state_1_id )
        self.assertEqual(atc.autoreclama_history_ids[1].change_date, state_1_dt )
        self.assertEqual(atc.autoreclama_history_ids[1].end_date, state_2_dt )
        self.assertEqual(atc.autoreclama_history_ids[1].atc_id.id, new_atc_id )
        self.assertEqual(atc.autoreclama_history_ids[1].generated_atc_id.id, state_1_st )

        self.assertEqual(atc.autoreclama_history_ids[2].state_id.id, state_0_id )
        self.assertEqual(atc.autoreclama_history_ids[2].change_date, state_0_dt )
        self.assertEqual(atc.autoreclama_history_ids[2].end_date, state_1_dt )
        self.assertEqual(atc.autoreclama_history_ids[2].atc_id.id, new_atc_id )
        self.assertEqual(atc.autoreclama_history_ids[2].generated_atc_id.id, False )


class SomAutoreclamaCreationWizardTest(SomAutoreclamaBaseTests):

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

        par1_id = self.search_in('res.partner', [('name','ilike','Tiny sprl')])
        par2_id = self.search_in('res.partner', [('name','ilike','ASUStek')])
        par_obj = self.get_model('res.partner')
        par_obj.write(self.cursor, self.uid, par1_id, {'ref':'58264'})
        par_obj.write(self.cursor, self.uid, par2_id, {'ref':'58265'})

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

        atr = self.browse_referenced(atc.ref)

        self.assertEqual(atr.proces_id.name, u'R1')
        self.assertEqual(atr.step_id.name, u'01')
        self.assertEqual(atr.section_id.name, u'Switching')
        self.assertEqual(atr.cups_polissa_id.id, polissa_id)
        self.assertEqual(atr.state, u'open')
        self.assertEqual(atr.ref, u'giscedata.atc, {}'.format(atc.id))

    def test_create_ATC_R1_029_from_atc_via_wizard__from_atr(self):
        atc_obj = self.get_model('giscedata.atc')

        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002')[1]

        par1_id = self.search_in('res.partner', [('name','ilike','Tiny sprl')])
        par2_id = self.search_in('res.partner', [('name','ilike','ASUStek')])
        par_obj = self.get_model('res.partner')
        par_obj.write(self.cursor, self.uid, par1_id, {'ref':'58264'})
        par_obj.write(self.cursor, self.uid, par2_id, {'ref':'58265'})

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

        new_atc_id = atc_obj.create_ATC_R1_029_from_atc_via_wizard(self.cursor, self.uid, old_atc_id, {})

        atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)
        atc_old = atc_obj.browse(self.cursor, self.uid, old_atc_id)

        self.assertEqual(atc.name , new_case_data['descripcio'])
        self.assertEqual(atc.canal_id.id , channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id , subtipus_id)
        self.assertEqual(atc.polissa_id.id , polissa_id)
        self.assertEqual(atc.tancar_cac_al_finalitzar_r1 , new_case_data['tanca_al_finalitzar_r1'])
        self.assertEqual(atc.state , 'pending')
        self.assertEqual(atc.agent_actual, '10')

        model, id = atc.ref.split(",")
        self.assertEqual(model, 'giscedata.switching')
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u'R1')
        self.assertEqual(ref.step_id.name, u'01')
        self.assertEqual(ref.section_id.name, u'Switching')
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u'open')
        self.assertEqual(ref.ref, u'giscedata.atc, {}'.format(atc.id))

        codi_solicitud_old =  self.browse_referenced(atc_old.ref).codi_sollicitud
        cas_atr = self.browse_referenced(atc.ref)
        pas_atr_id = cas_atr.step_ids[0].pas_id
        pas_atr = self.browse_referenced(pas_atr_id)
        codi_solicitud_ref = pas_atr.reclamacio_ids[0].codi_sollicitud_reclamacio
        self.assertEqual(codi_solicitud_old, codi_solicitud_ref)


class SomAutoreclamaEzATC_Test(SomAutoreclamaBaseTests):

    def build_atc(self, subtype='029', r1=False, channel='intercambi', section='client', log_days=3, agent_actual='10', state='pending', active=True):
        atc_obj = self.get_model('giscedata.atc')
        ir_obj = self.get_model('ir.model.data')
        polissa_id = ir_obj.get_object_reference(self.cursor, self.uid, 'giscedata_polissa', 'polissa_0002')[1]

        par1_id = self.search_in('res.partner', [('name','ilike','Tiny sprl')])
        par2_id = self.search_in('res.partner', [('name','ilike','ASUStek')])
        par_obj = self.get_model('res.partner')
        par_obj.write(self.cursor, self.uid, par1_id, {'ref':'58264'})
        par_obj.write(self.cursor, self.uid, par2_id, {'ref':'58265'})

        channel_id = self.search_in('res.partner.canal', [('name','ilike',channel)])
        section_id = self.search_in('crm.case.section', [('name','ilike',section)])
        subtipus_id = self.search_in('giscedata.subtipus.reclamacio', [('name','=',subtype)])

        new_case_data = {
            'polissa_id': polissa_id,
            'descripcio': u'Reclamació per retràs automàtica',
            'canal_id': channel_id,
            'section_id': section_id,
            'subtipus_reclamacio_id': subtipus_id,
            'comentaris': u'test test test',
            'sense_responsable': True,
            'tanca_al_finalitzar_r1': r1,
            'crear_cas_r1': r1,
        }
        atc_id = atc_obj.create_general_atc_r1_case_via_wizard(self.cursor, self.uid, new_case_data, {})

        atc_obj.write(self.cursor, self.uid, atc_id, {
                'agent_actual':agent_actual,
                'state': state,
                'active': active,
            })
        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        log_obj = self.get_model('crm.case.log')
        log_obj.write(self.cursor, self.uid, atc.log_ids[1].id, {'date':today_minus_str(log_days)})

        return atc_id


class SomAutoreclamaConditionsTest(SomAutoreclamaEzATC_Test):

    def test_fit_atc_condition__001_c_no(self):
        ir_obj = self.get_model('ir.model.data')
        atc_obj = self.get_model('giscedata.atc')
        cond_obj = self.get_model('som.autoreclama.state.condition')

        atc_id = self.build_atc(subtype='001', log_days=10)
        atc_data = atc_obj.get_autoreclama_data(self.cursor, self.uid, atc_id, {})

        cond_id = ir_obj.get_object_reference(self.cursor, self.uid, 'som_autoreclama', 'conditions_001_correct_state_workflow_atc')[1]

        ok = cond_obj.fit_atc_condition(self.cursor, self.uid, cond_id, atc_data, {})
        self.assertEqual(ok, False)

    def test_fit_atc_condition__001_c_yes(self):
        ir_obj = self.get_model('ir.model.data')
        atc_obj = self.get_model('giscedata.atc')
        cond_obj = self.get_model('som.autoreclama.state.condition')

        atc_id = self.build_atc(subtype='001', log_days=50, r1=True)
        atc_data = atc_obj.get_autoreclama_data(self.cursor, self.uid, atc_id, {})

        cond_id = ir_obj.get_object_reference(self.cursor, self.uid, 'som_autoreclama', 'conditions_001_correct_state_workflow_atc')[1]

        ok = cond_obj.fit_atc_condition(self.cursor, self.uid, cond_id, atc_data, {})
        self.assertEqual(ok, True)

    def test_fit_atc_condition__some(self):
        ir_obj = self.get_model('ir.model.data')
        atc_obj = self.get_model('giscedata.atc')
        cond_obj = self.get_model('som.autoreclama.state.condition')

        test_datas = [
            {'subtype':'001', 'log_days':30/2, 'result':False ,'cond':'conditions_001_correct_state_workflow_atc'},
            {'subtype':'001', 'log_days':30*2, 'result':True  ,'cond':'conditions_001_correct_state_workflow_atc'},
            {'subtype':'038', 'log_days':30/2, 'result':False ,'cond':'conditions_038_correct_state_workflow_atc'},
            {'subtype':'038', 'log_days':30*2, 'result':True  ,'cond':'conditions_038_correct_state_workflow_atc'},
            {'subtype':'027', 'log_days':10/2, 'result':False ,'cond':'conditions_027_correct_state_workflow_atc'},
            {'subtype':'027', 'log_days':10*2, 'result':True  ,'cond':'conditions_027_correct_state_workflow_atc'},
            {'subtype':'039', 'log_days':30/2, 'result':False ,'cond':'conditions_039_correct_state_workflow_atc'},
            {'subtype':'039', 'log_days':30*2, 'result':True  ,'cond':'conditions_039_correct_state_workflow_atc'},
        ]

        for test_data in test_datas:
            atc_id = self.build_atc(subtype=test_data['subtype'], log_days=test_data['log_days'], r1=True)
            atc_data = atc_obj.get_autoreclama_data(self.cursor, self.uid, atc_id, {})

            cond_id = ir_obj.get_object_reference(self.cursor, self.uid, 'som_autoreclama', test_data['cond'])[1]

            ok = cond_obj.fit_atc_condition(self.cursor, self.uid, cond_id, atc_data, {})
            self.assertEqual(ok, test_data['result'])

    def test_fit_atc_condition__all(self):
        atc_obj = self.get_model('giscedata.atc')
        cond_obj = self.get_model('som.autoreclama.state.condition')

        cond_ids = cond_obj.search(self.cursor, self.uid, [])
        for cond_id in cond_ids:
            cond = cond_obj.browse(self.cursor, self.uid, cond_id)

            print cond.subtype_id.name
            if cond.subtype_id.name == '006': # unsuported
                continue

            # test more
            atc_id = self.build_atc(subtype=cond.subtype_id.name, log_days=cond.days * 2, r1=True)
            atc_data = atc_obj.get_autoreclama_data(self.cursor, self.uid, atc_id, {})
            ok = cond_obj.fit_atc_condition(self.cursor, self.uid, cond_id, atc_data, {})
            self.assertEqual(ok, True, "Error on More than for condition id {}".format(cond_id))

            # test less
            atc_id = self.build_atc(subtype=cond.subtype_id.name, log_days=cond.days / 2, r1=True)
            atc_data = atc_obj.get_autoreclama_data(self.cursor, self.uid, atc_id, {})
            ok = cond_obj.fit_atc_condition(self.cursor, self.uid, cond_id, atc_data, {})
            self.assertEqual(ok, False, "Error on Less than for condition id {}".format(cond_id))


class SomAutoreclamaUpdaterTest(SomAutoreclamaEzATC_Test):

    def test_get_atc_candidates_to_update__all(self):
        atc_ids = []

        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())

        updtr_obj = self.get_model('som.autoreclama.state.updater')
        atcs = updtr_obj.get_atc_candidates_to_update(self.cursor, self.uid)

        self.assertEqual(set(atc_ids) & set(atcs), set(atc_ids))
        self.assertTrue(len(atcs) >= 7)

    def test_get_atc_candidates_to_update__none(self):
        atc_ids = []

        atc_ids.append(self.build_atc(active=False))
        atc_ids.append(self.build_atc(state='open'))
        atc_ids.append(self.build_atc(agent_actual='06'))
        atc_ids.append(self.build_atc())
        state_d_id = self.search_in('som.autoreclama.state', [('name','ilike','desact')])
        history_obj = self.get_model('som.autoreclama.state.history.atc')
        history_obj.historize(self.cursor, self.uid, atc_ids[-1], state_d_id, today_str(), False)

        updtr_obj = self.get_model('som.autoreclama.state.updater')
        atcs = updtr_obj.get_atc_candidates_to_update(self.cursor, self.uid)

        self.assertEqual(set(atcs), set())

    def test_get_atc_candidates_to_update__some(self):
        atc_ids = []

        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc())
        atc_ids.append(self.build_atc(active=False))
        atc_ids.append(self.build_atc(state='open'))
        atc_ids.append(self.build_atc(agent_actual='06'))
        atc_ids.append(self.build_atc())
        state_d_id = self.search_in('som.autoreclama.state', [('name','ilike','desact')])
        history_obj = self.get_model('som.autoreclama.state.history.atc')
        history_obj.historize(self.cursor, self.uid, atc_ids[-1], state_d_id, today_str(), False)

        updtr_obj = self.get_model('som.autoreclama.state.updater')
        atcs = updtr_obj.get_atc_candidates_to_update(self.cursor, self.uid)

        self.assertEqual(set(atc_ids[:2]) & set(atcs), set(atc_ids[:2]))
        self.assertEqual(set(atc_ids[2:]) & set(atcs), set())
        self.assertTrue(len(atcs) >= 2)

    def test_update_atc_if_possible__no_condition_meet(self):
        atc_id = self.build_atc()

        updtr_obj = self.get_model('som.autoreclama.state.updater')
        status, message = updtr_obj.update_atc_if_possible(self.cursor, self.uid, atc_id, {})

        self.assertEqual(status, False)
        self.assertTrue(message.startswith(u'No compleix cap condici\xf3 activa, examinades '))
        self.assertTrue(message.endswith(u'condicions.'))
        self.assertTrue(int(message[44:46]) >= 59)

    def test_update_atc_if_possible__do_action_test(self):
        atc_obj = self.get_model('giscedata.atc')

        atc_id = self.build_atc(log_days=60, subtype='001', r1=True)

        updtr_obj = self.get_model('som.autoreclama.state.updater')
        status, message = updtr_obj.update_atc_if_possible(self.cursor, self.uid, atc_id, {'search_only':True})

        self.assertEqual(status, True)
        self.assertEqual(message, u"Testing")

    def test_update_atc_if_possible__do_action_full(self):
        atc_obj = self.get_model('giscedata.atc')

        atc_id = self.build_atc(log_days=60, subtype='001', r1=True)

        updtr_obj = self.get_model('som.autoreclama.state.updater')
        status, message = updtr_obj.update_atc_if_possible(self.cursor, self.uid, atc_id, {})

        self.assertEqual(status, True)
        self.assertTrue(message.startswith(u'Estat Primera reclamacio executat, nou atc creat amb id '))

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        self.assertGreaterEqual(atc.business_days_with_same_agent, 30)
        self.assertEqual(atc.agent_actual, u'10')
        self.assertEqual(atc.autoreclama_state.name, u'Primera reclamacio')
        self.assertEqual(atc.autoreclama_state_date, today_str())
        self.assertGreaterEqual(len(atc.autoreclama_history_ids), 2)

    def test_update_atcs_if_possible__some_consitions(self):
        atc_n_id = self.build_atc(r1=True)
        atc_y_id = self.build_atc(log_days=60, subtype='001', r1=True)

        updtr_obj = self.get_model('som.autoreclama.state.updater')
        up, not_up, error, msg = updtr_obj.update_atcs_if_possible(self.cursor, self.uid, [atc_y_id, atc_n_id], {})

        self.assertEqual(up, [atc_y_id])
        self.assertEqual(not_up, [atc_n_id])
        self.assertEqual(error, [])


class SomAutoreclamaDoActionTest(SomAutoreclamaEzATC_Test):

    def test_do_action__deactivated(self):
        atc_obj = self.get_model('giscedata.atc')
        state_obj = self.get_model('som.autoreclama.state')

        atc_id = self.build_atc(log_days=60, subtype='001')

        ir_obj = self.get_model('ir.model.data')
        state_id = ir_obj.get_object_reference(self.cursor, self.uid, 'som_autoreclama', 'disabled_state_workflow_atc')[1]
        state_obj.write(self.cursor, self.uid, state_id, {'active':False})
        state = state_obj.browse(self.cursor, self.uid, state_id)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        pre_atc_history_len = len(atc.autoreclama_history_ids)
        pre_atc_state_name = atc.autoreclama_state.name
        pre_atc_data = str(atc.read())

        result = state_obj.do_action(self.cursor, self.uid, state_id, atc_id, {})

        self.assertEqual(result['do_change'], False)
        self.assertEqual(result['message'], u'Estat {} desactivat!'.format(state.name))
        self.assertTrue('created_atc' not in result)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id) # no changes
        self.assertEqual(pre_atc_history_len, len(atc.autoreclama_history_ids))
        self.assertEqual(pre_atc_state_name, atc.autoreclama_state.name)
        self.assertEqual(pre_atc_data, str(atc.read()))

    def test_do_action__no_action(self):
        atc_obj = self.get_model('giscedata.atc')
        state_obj = self.get_model('som.autoreclama.state')

        atc_id = self.build_atc(log_days=60, subtype='001')

        ir_obj = self.get_model('ir.model.data')
        state_id = ir_obj.get_object_reference(self.cursor, self.uid, 'som_autoreclama', 'correct_state_workflow_atc')[1]
        state = state_obj.browse(self.cursor, self.uid, state_id)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        pre_atc_history_len = len(atc.autoreclama_history_ids)
        pre_atc_state_name = atc.autoreclama_state.name
        pre_atc_data = str(atc.read())

        result = state_obj.do_action(self.cursor, self.uid, state_id, atc_id, {})

        self.assertEqual(result['do_change'], True)
        self.assertEqual(result['message'], u'Estat {} sense acció --> Ok'.format(state.name))
        self.assertTrue('created_atc' not in result)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id) # no changes
        self.assertEqual(pre_atc_history_len, len(atc.autoreclama_history_ids))
        self.assertEqual(pre_atc_state_name, atc.autoreclama_state.name)
        self.assertEqual(pre_atc_data, str(atc.read()))

    def test_do_action__ok(self):
        atc_obj = self.get_model('giscedata.atc')
        state_obj = self.get_model('som.autoreclama.state')

        atc_id = self.build_atc(log_days=60, subtype='001', r1=True)

        ir_obj = self.get_model('ir.model.data')
        state_id = ir_obj.get_object_reference(self.cursor, self.uid, 'som_autoreclama', 'first_state_workflow_atc')[1]
        state = state_obj.browse(self.cursor, self.uid, state_id)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        pre_atc_history_len = len(atc.autoreclama_history_ids)
        pre_atc_state_name = atc.autoreclama_state.name
        pre_atc_data = str(atc.read())

        result = state_obj.do_action(self.cursor, self.uid, state_id, atc_id, {})

        self.assertEqual(result['do_change'], True)
        self.assertEqual(result['message'], u'Estat {} executat, nou atc creat amb id {}'.format(state.name, result['created_atc']))
        self.assertGreaterEqual(result['created_atc'], atc_id)
        new_atc_id = result['created_atc']

        atc = atc_obj.browse(self.cursor, self.uid, atc_id) # no changes
        self.assertEqual(pre_atc_history_len, len(atc.autoreclama_history_ids))
        self.assertEqual(pre_atc_state_name, atc.autoreclama_state.name)
        self.assertEqual(pre_atc_data, str(atc.read()))

        new_atc = atc_obj.browse(self.cursor, self.uid, new_atc_id)
        # automated atc creation covered by test_create_ATC_R1_029_from_atc_via_wizard__from_atr

    def test_do_action__error(self):
        atc_obj = self.get_model('giscedata.atc')
        state_obj = self.get_model('som.autoreclama.state')

        atc_id = self.build_atc(log_days=60, subtype='001')

        ir_obj = self.get_model('ir.model.data')
        state_id = ir_obj.get_object_reference(self.cursor, self.uid, 'som_autoreclama', 'first_state_workflow_atc')[1]
        state_obj.write(self.cursor, self.uid, state_id, {
            'generate_atc_parameters_text':'{"model": "giscedata.atc", "method": "create_ATC_R1_029_from_atc_via_wizard_ERROR"}',
        })
        error_message = u"'crm.case' object has no attribute 'create_ATC_R1_029_from_atc_via_wizard_ERROR'"
        state = state_obj.browse(self.cursor, self.uid, state_id)

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        pre_atc_history_len = len(atc.autoreclama_history_ids)
        pre_atc_state_name = atc.autoreclama_state.name
        pre_atc_data = str(atc.read())

        result = state_obj.do_action(self.cursor, self.uid, state_id, atc_id, {})

        self.assertEqual(result['do_change'], False)
        self.assertTrue(result['message'].startswith(u'Execuci\xf3 d\'accions del estat {} genera ERROR'.format(state.name)))

        atc = atc_obj.browse(self.cursor, self.uid, atc_id) # no changes
        self.assertEqual(pre_atc_history_len, len(atc.autoreclama_history_ids))
        self.assertEqual(pre_atc_state_name, atc.autoreclama_state.name)
        self.assertEqual(pre_atc_data, str(atc.read()))
