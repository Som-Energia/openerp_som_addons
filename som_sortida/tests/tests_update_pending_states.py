from destral import testing
from base_extended_som.tests.utils import avoid_creating_subcursors


class TestUpdatePendingStates(testing.OOTestCaseWithCursor):

    def test_update_state(self):
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
        estat_falta_un_mes = imd_obj.get_object_reference(
            cursor, uid, 'som_sortida', 'enviar_cor_falta_un_mes_pending_state'
        )[1]
        pol = pol_obj.browse(cursor, uid, polissa_id)
        self.assertEqual(pol.sortida_state_id.id, estat_sense_socia)

        # Call the method to test
        wiz_id = upd_obj.create(cursor, uid, {}, context=None)
        wiz = upd_obj.browse(cursor, uid, wiz_id)
        history_values = {
            'pending_state_id': estat_sense_socia,
            'change_date': '2023-10-01'
        }
        wiz.update_state(polissa_id, history_values)

        # Assert the expected outcome
        pol = pol_obj.browse(cursor, uid, polissa_id)
        self.assertEqual(pol.sortida_state_id.id, estat_falta_un_mes)
        self.assertTrue(pol.en_process_de_sortida)
        hist_id = hist_obj.search(cursor, uid, [('polissa_id', '=', polissa_id)])
        hist_data = hist_obj.read(cursor, uid, hist_id, ['pending_state_id', 'change_date'])
        self.assertEqual(hist_data[-1]['pending_state_id'][0], estat_falta_un_mes)

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

        pol_obj.set_pending(cursor, uid, polissa_id, estat_sense_socia_id, {
            'custom_change_dates': {polissa_id: '2023-10-01'},
        })

        wiz_id = upd_obj.create(cursor, uid, {}, context=None)
        wiz = upd_obj.browse(cursor, uid, wiz_id)

        with avoid_creating_subcursors(cursor):
            wiz.update_polisses()

        pol = pol_obj.browse(cursor, uid, polissa_id)

        self.assertEqual(pol.sortida_state_id.id, estat_1m_id)

        outbox_mail_ids = mailbox_obj.search(cursor, uid, [
            ('template_id', '=', email_ct_ss_1mes_id),
            ('folder', '=', 'outbox'),
        ])
        self.assertTrue(len(outbox_mail_ids) > 0)

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

        pol_obj.set_pending(cursor, uid, polissa_id, estat_1m_id, {
            'custom_change_dates': {polissa_id: '2023-10-01'},
        })

        wiz_id = upd_obj.create(cursor, uid, {}, context=None)
        wiz = upd_obj.browse(cursor, uid, wiz_id)

        with avoid_creating_subcursors(cursor):
            wiz.update_polisses()

        pol = pol_obj.browse(cursor, uid, polissa_id)

        self.assertEqual(pol.sortida_state_id.id, estat_15d_id)

        outbox_mail_ids = mailbox_obj.search(cursor, uid, [
            ('template_id', '=', email_ct_ss_15dies_id),
            ('folder', '=', 'outbox'),
        ])
        self.assertTrue(len(outbox_mail_ids) > 0)
