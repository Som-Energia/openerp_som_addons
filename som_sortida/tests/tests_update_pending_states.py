from destral import testing
from base_extended_som.tests.utils import avoid_creating_subcursors


class TestUpdatePendingStates(testing.OOTestCaseWithCursor):

    def test_update_sortida_state(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        upd_obj = self.openerp.pool.get('update.pending.states')
        hist_obj = self.openerp.pool.get('som.sortida.history')
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        estat_sense_socia = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state'
        )[1]
        estat_pendent_falta_un_mes = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_pendent_falta_un_mes_pending_state'
        )[1]
        pol = pol_obj.browse(cursor, uid, polissa_id)
        self.assertEqual(pol.sortida_state_id.id, estat_sense_socia)

        # Call the method to test
        history_values = {
            'pending_state_id': estat_sense_socia,
            'change_date': '2023-10-01'
        }
        upd_obj.update_sortida_state(cursor, uid, polissa_id, history_values)

        # Assert the expected outcome
        pol = pol_obj.browse(cursor, uid, polissa_id)
        self.assertEqual(pol.sortida_state_id.id, estat_pendent_falta_un_mes)
        self.assertTrue(pol.en_process_de_sortida)
        hist_id = hist_obj.search(cursor, uid, [('polissa_id', '=', polissa_id)])
        hist_data = hist_obj.read(cursor, uid, hist_id, ['pending_state_id', 'change_date'])
        self.assertEqual(hist_data[-1]['pending_state_id'][0], estat_pendent_falta_un_mes)

    def test_gicedata_update_workflow_30d(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        upd_obj = self.openerp.pool.get('update.pending.states')
        mailbox_obj = self.openerp.pool.get('poweremail.mailbox')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        estat_sense_socia_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state'
        )[1]
        estat_1m_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_falta_un_mes_pending_state'
        )[1]

        email_ct_ss_1mes_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'email_ct_ss_1mes'
        )[1]
        old_total_outbox_mails = mailbox_obj.search_count(cursor, uid, [
            ('template_id', '=', email_ct_ss_1mes_id),
            ('folder', '=', 'outbox'),
        ])

        pol_obj.send_signal(cursor, uid, [polissa_id], [
            "validar", "contracte"
        ])

        # Soci with valid phone number
        partner_soci_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa_soci', 'res_partner_soci_ct'
        )[1]
        pol_obj.write(cursor, uid, [polissa_id], {'soci': partner_soci_id})

        pol_obj.set_pending(cursor, uid, polissa_id, estat_sense_socia_id, {
            'custom_change_dates': {polissa_id: '2023-10-01'},
        })

        with avoid_creating_subcursors(cursor):
            upd_obj.update_polisses(cursor, uid)

        pol = pol_obj.browse(cursor, uid, polissa_id)

        self.assertEqual(pol.sortida_state_id.id, estat_1m_id)

        new_total_outbox_mails = mailbox_obj.search_count(cursor, uid, [
            ('template_id', '=', email_ct_ss_1mes_id),
            ('folder', '=', 'outbox'),
        ])
        self.assertGreater(new_total_outbox_mails, old_total_outbox_mails)

    def test_gicedata_update_workflow_15d(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        upd_obj = self.openerp.pool.get('update.pending.states')
        mailbox_obj = self.openerp.pool.get('poweremail.mailbox')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        estat_1m_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_falta_un_mes_pending_state'
        )[1]
        estat_15d_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_falta_15_dies_pending_state'
        )[1]

        email_ct_ss_15dies_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'email_ct_ss_15dies'
        )[1]
        old_total_outbox_mails = mailbox_obj.search_count(cursor, uid, [
            ('template_id', '=', email_ct_ss_15dies_id),
            ('folder', '=', 'outbox'),
        ])

        pol_obj.send_signal(cursor, uid, [polissa_id], [
            "validar", "contracte"
        ])

        pol_obj.set_pending(cursor, uid, polissa_id, estat_1m_id, {
            'custom_change_dates': {polissa_id: '2023-10-01'},
        })

        with avoid_creating_subcursors(cursor):
            upd_obj.update_polisses(cursor, uid)

        pol = pol_obj.browse(cursor, uid, polissa_id)

        self.assertEqual(pol.sortida_state_id.id, estat_15d_id)

        new_total_outbox_mails = mailbox_obj.search_count(cursor, uid, [
            ('template_id', '=', email_ct_ss_15dies_id),
            ('folder', '=', 'outbox'),
        ])
        self.assertGreater(new_total_outbox_mails, old_total_outbox_mails)

    def test_gicedata_update_workflow_7d(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        upd_obj = self.openerp.pool.get('update.pending.states')
        smsbox_obj = self.openerp.pool.get('powersms.smsbox')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        partner_soci_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa_soci', 'res_partner_soci'
        )[1]
        estat_15d_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_falta_15_dies_pending_state'
        )[1]
        estat_7d_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_falta_7_dies_pending_state'
        )[1]

        pol_obj.send_signal(cursor, uid, [polissa_id], [
            "validar", "contracte"
        ])

        old_total_outbox_sms = smsbox_obj.search_count(cursor, uid, [
            ('psms_body_text', 'like', '%renovar%'),
            ('folder', '=', 'outbox'),
        ])

        # We need a titular with valid phone number
        pol_obj.write(cursor, uid, [polissa_id], {'titular': partner_soci_id})

        pol_obj.set_pending(cursor, uid, polissa_id, estat_15d_id, {
            'custom_change_dates': {polissa_id: '2023-10-01'},
        })

        with avoid_creating_subcursors(cursor):
            upd_obj.update_polisses(cursor, uid)

        pol = pol_obj.browse(cursor, uid, polissa_id)

        self.assertEqual(pol.sortida_state_id.id, estat_7d_id)

        new_total_outbox_sms = smsbox_obj.search_count(cursor, uid, [
            ('psms_body_text', 'like', '%renovar%'),
            ('folder', '=', 'outbox'),
        ])
        self.assertGreater(new_total_outbox_sms, old_total_outbox_sms)

    def test_gicedata_update_workflow_b1(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        upd_obj = self.openerp.pool.get('update.pending.states')
        sw_obj = self.openerp.pool.get('giscedata.switching')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        estat_7d_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_falta_7_dies_pending_state'
        )[1]
        estat_b1_creat_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_cas_b1_creat_pending_state'
        )[1]

        partner_soci_id = imd_obj.get_object_reference(
            cursor, uid, 'som_polissa_soci', 'res_partner_soci_ct'
        )[1]
        pol_obj.write(cursor, uid, [polissa_id], {'soci': partner_soci_id}, context={
            'custom_change_dates': {polissa_id: '2023-09-01'},
        })
        pol_obj.send_signal(cursor, uid, [polissa_id], [
            "validar", "contracte"
        ])

        pol_obj.set_pending(cursor, uid, polissa_id, estat_7d_id, {
            'custom_change_dates': {polissa_id: '2023-10-01'},
        })

        with avoid_creating_subcursors(cursor):
            upd_obj.update_polisses(cursor, uid)

        pol = pol_obj.browse(cursor, uid, polissa_id)

        self.assertEqual(pol.sortida_state_id.id, estat_b1_creat_id)

        atr_case = sw_obj.search(
            cursor, uid, [
                ("cups_polissa_id", "=", polissa_id),
                ("proces_id.name", "=", "B1"),
                ("state", "in", ["draft", "open"]),
            ]
        )
        self.assertEqual(len(atr_case), 1)

    def test_gicedata_update_workflow_b1_fails(self):
        cursor = self.cursor
        uid = self.uid
        imd_obj = self.openerp.pool.get('ir.model.data')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        upd_obj = self.openerp.pool.get('update.pending.states')

        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001'
        )[1]
        estat_7d_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_falta_7_dies_pending_state'
        )[1]
        estat_b1_error_id = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_cas_b1_error_pending_state'
        )[1]

        pol_obj.send_signal(cursor, uid, [polissa_id], [
            "validar", "contracte"
        ])

        pol_obj.set_pending(cursor, uid, polissa_id, estat_7d_id, {
            'custom_change_dates': {polissa_id: '2023-10-01'},
        })

        # draft polissa and no CT SS soci, it will fail
        with avoid_creating_subcursors(cursor):
            upd_obj.update_polisses(cursor, uid)

        pol = pol_obj.browse(cursor, uid, polissa_id)

        self.assertEqual(pol.sortida_state_id.id, estat_b1_error_id)

        # When updating again, it should stay in the same state
        with avoid_creating_subcursors(cursor):
            upd_obj.update_polisses(cursor, uid)
        self.assertEqual(pol.sortida_state_id.id, estat_b1_error_id)
