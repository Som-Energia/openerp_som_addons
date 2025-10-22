# -*- coding: utf-8 -*-
from osv import osv
from destral import testing
from datetime import datetime
import mock


class TestsGiscedataPolissa(testing.OOTestCaseWithCursor):
    def test_giscedata_polissa_te_socia_real_vinculada(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        pol = pol_obj.browse(cursor, uid, polissa_id)
        # Considerem sense sòcia com a socia real vinculada
        self.assertTrue(pol.te_socia_real_vinculada,
                        "La pòlissa hauria de tenir sòcia real vinculada")

        soci_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa_soci', 'soci_0001'
        )[1]
        pol_obj.write(cursor, uid, [polissa_id], {'soci': soci_id})
        pol = pol_obj.browse(cursor, uid, polissa_id)
        self.assertTrue(pol.te_socia_real_vinculada,
                        "La pòlissa hauria de ser amb sòcia real vinculada")

    def test_giscedata_polissa_sortida_state(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        pol = pol_obj.browse(cursor, uid, polissa_id)
        # Check initial state
        self.assertEqual(
            pol.sortida_state_id.name, 'Contrate sense sòcia',
            "L'estat inicial hauria de ser 'Contrate sense sòcia' en comptes de {}".format(
                pol.sortida_state_id.name
            ))

    def tests_gicedata_polissa_history(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        hist_obj = self.openerp.pool.get('som.sortida.history')
        pol_obj = self.openerp.pool.get('giscedata.polissa')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        pol_obj.write(cursor, uid, polissa_id, {'soci': False})
        hist_id = hist_obj.search(cursor, uid, [('polissa_id', '=', polissa_id)])
        self.assertTrue(hist_id, "No s'ha trobat cap historial per a la pòlissa")

        hist_data = hist_obj.read(cursor, uid, hist_id, ['polissa_id'])
        self.assertEqual(hist_data[0]['polissa_id'][0], polissa_id,
                         "L'historial hauria de correspondre a la pòlissa correcta")

    def test_gicedata_polissa_to_cor_date(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        estat_sense_socia = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state'
        )[1]
        estat_15d = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_falta_15_dies_pending_state'
        )[1]
        estat_enivat = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_enviat_cor_pending_state'
        )[1]

        pol_obj.set_pending(cursor, uid, polissa_id, estat_sense_socia, {
            'custom_change_dates': {polissa_id: '2023-10-01'},
        })
        cor_submission_date = pol_obj.read(
            cursor, uid, polissa_id, ['cor_submission_date']
        )['cor_submission_date']
        self.assertEqual(cor_submission_date, datetime(2024, 9, 30, 0, 0))

        pol_obj.set_pending(cursor, uid, polissa_id, estat_15d, {
            'custom_change_dates': {polissa_id: '2024-10-01'},
        })
        cor_submission_date = pol_obj.read(
            cursor, uid, polissa_id, ['cor_submission_date']
        )['cor_submission_date']
        self.assertEqual(cor_submission_date, datetime(2024, 10, 16, 0, 0))

        pol_obj.set_pending(cursor, uid, polissa_id, estat_enivat, {
            'custom_change_dates': {polissa_id: '2024-11-01'},
        })
        cor_submission_date = pol_obj.read(
            cursor, uid, polissa_id, ['cor_submission_date']
        )['cor_submission_date']
        self.assertEqual(cor_submission_date, datetime(2024, 11, 1, 0, 0))

    def test_request_submission_to_cor(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get("ir.model.data")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        sw_obj = self.openerp.pool.get("giscedata.switching")

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "polissa_0001"
        )[1]
        pol_obj.send_signal(cursor, uid, [polissa_id], [
            "validar", "contracte"
        ])

        partner_soci_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa_soci', 'res_partner_soci_ct'
        )[1]
        pol_obj.write(cursor, uid, [polissa_id], {'soci': partner_soci_id})

        estat_pendent_cor = imd_obj.get_object_reference(
            cursor, uid, "som_sortida", "enviar_cor_pendent_crear_b1_dies_pending_state"
        )[1]
        pol_obj.set_pending(cursor, uid, polissa_id, estat_pendent_cor, {
            "custom_change_dates": {polissa_id: "2025-08-15"},
        })
        case_id = pol_obj.request_submission_to_cor(cursor, uid, polissa_id)

        b1 = sw_obj.browse(cursor, uid, case_id)

        self.assertEqual(b1.proces_id.name, "B1")
        self.assertEqual(b1.state, "open")
        self.assertEqual(b1.notificacio_pendent, True)
        self.assertEqual(b1.step_id.name, "01")

        b101 = sw_obj.get_pas(cursor, uid, b1)
        self.assertEqual(b101.data_accio, datetime.today().strftime("%Y-%m-%d"))
        self.assertEqual(b101.activacio, "A")

    def test_request_submission_to_cor_not_possible(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get("ir.model.data")
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "polissa_0001"
        )[1]
        pol_obj.send_signal(cursor, uid, [polissa_id], [
            "validar", "contracte"
        ])

        partner_soci_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa_soci', 'res_partner_soci_ct'
        )[1]
        pol_obj.write(cursor, uid, [polissa_id], {'soci': partner_soci_id})

        estat_pendent_cor = imd_obj.get_object_reference(
            cursor, uid, "som_sortida", "enviar_cor_pendent_crear_b1_dies_pending_state"
        )[1]
        pol_obj.set_pending(cursor, uid, polissa_id, estat_pendent_cor, {
            "custom_change_dates": {polissa_id: "2025-08-15"},
        })

        # With an open ATR case it can't be submitted to COR
        pol_obj.crear_cas_atr(cursor, uid, polissa_id, proces="M1")

        with self.assertRaises(osv.except_osv):
            pol_obj.request_submission_to_cor(cursor, uid, polissa_id)

    @mock.patch('som_sortida.models.res_partner_address.ResPartnerAddress.subscribe_polissa_titular_in_ctss_lists')  # noqa: E501
    def test__write__add_category_ct_sense_socia(self, mocked_subscribe):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get("ir.model.data")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_polissa", "polissa_0001"
        )[1]
        # Put category CT sense sòcia
        category_cts_sense_socia_id = imd_obj.get_object_reference(
            cursor, uid, "som_polissa_soci", "origen_ct_sense_socia_category"
        )[1]

        pol_obj.write(cursor, uid, [polissa_id], {
            'category_id': [(3, category_cts_sense_socia_id)]
        })

        mocked_subscribe.assert_called_once_with(
            cursor, uid, [polissa_id], context={}
        )
