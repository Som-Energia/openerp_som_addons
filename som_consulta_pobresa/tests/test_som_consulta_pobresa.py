# -*- coding: utf-8 -*-
from osv import osv
from destral import testing
from destral.transaction import Transaction


class TestConsultaPobresa(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_resolution_not_defined_when_close(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get('som.consulta.pobresa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        cons_id = imd_obj.get_object_reference(
            cursor, uid,
            'som_consulta_pobresa', 'som_consulta_pobresa_demo_record'
        )[1]

        with self.assertRaises(osv.except_osv) as e:
            cons_obj.close_case(cursor, uid, [cons_id])

        self.assertEqual(
            e.exception.message,
            "warning -- Falta resoluci\xc3\xb3\n\nPer poder tancar la consulta s'ha d'informar el camp resolució."  # noqa: E501
        )

    def test_resolution_defined_when_close(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get('som.consulta.pobresa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        cons_id = imd_obj.get_object_reference(
            cursor, uid,
            'som_consulta_pobresa', 'som_consulta_pobresa_demo_record'
        )[1]
        cons_obj.write(cursor, uid, cons_id, {'resolucio': 'positiva'})

        cons_obj.close_case(cursor, uid, [cons_id])

        state = cons_obj.read(cursor, uid, cons_id, ['state'])['state']
        self.assertEqual(state, 'done')

    def test_consulta_pobresa_activa_none(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get('som.consulta.pobresa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0001')[1]
        partner_id = imd_obj.get_object_reference(
            cursor, uid, 'base', 'res_partner_asus')[1]

        result = cons_obj.consulta_pobresa_activa(cursor, uid, [], partner_id, polissa_id)

        self.assertFalse(result)

    def test_consulta_pobresa_activa_any(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get('som.consulta.pobresa')
        imd_obj = self.openerp.pool.get('ir.model.data')
        cons_id = imd_obj.get_object_reference(
            cursor, uid,
            'som_consulta_pobresa', 'som_consulta_pobresa_demo_record'
        )[1]
        polissa_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0002')[1]
        partner_id = imd_obj.get_object_reference(
            cursor, uid, 'base', 'res_partner_asus')[1]
        cons_obj.write(cursor, uid, cons_id, {'resolucio': 'positiva'})
        cons_obj.close_case(cursor, uid, [cons_id])

        result = cons_obj.consulta_pobresa_activa(cursor, uid, [], partner_id, polissa_id)

        self.assertTrue(result)

    def test_moure_factures_pobresa_only_unpaid_invoices(self):
        cursor = self.cursor
        uid = self.uid
        cons_obj = self.openerp.pool.get('som.consulta.pobresa')
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        gff_obj = self.openerp.pool.get('giscedata.facturacio.factura')
        imd_obj = self.openerp.pool.get('ir.model.data')
        cups_obj = self.openerp.pool.get('giscedata.cups.ps')
        pol_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0002'
        )[1]
        process_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social',
            'bono_social_pending_state_process'
        )[1]
        pol_obj.write(cursor, uid, pol_id, {'state': 'activa', 'process_id': process_id})
        pol = pol_obj.browse(cursor, uid, pol_id)
        consulta_state_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending',
            'pendent_consulta_probresa_pending_state',
        )[1]
        pobresa_state_id = imd_obj.get_object_reference(
            cursor, uid, 'som_account_invoice_pending',
            'probresa_energetica_certificada_pending_state',
        )[1]
        correcte_state_id = imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social',
            'correct_bono_social_pending_state',
        )[1]
        partner_id = imd_obj.get_object_reference(
            cursor, uid, 'base', 'res_partner_asus')[1]
        fact_id = imd_obj.get_object_reference(
            cursor, uid, 'som_consulta_pobresa', 'factura_conceptes_0001',
        )[1]
        fact3_id = imd_obj.get_object_reference(
            cursor, uid, 'som_consulta_pobresa', 'factura_conceptes_0003',
        )[1]
        consulta_id = imd_obj.get_object_reference(
            cursor, uid, 'som_consulta_pobresa', 'som_consulta_pobresa_demo_record',
        )[1]
        girona_id = imd_obj.get_object_reference(
            cursor, uid, 'l10n_ES_toponyms', 'ES17',
        )[1]
        cups_obj.write(cursor, uid, pol.cups.id, {'id_provincia': girona_id})
        fact3 = gff_obj.browse(cursor, uid, fact3_id)
        fact3.write({
            'state': 'open',
            'type': 'out_invoice',
            'pending_state': correcte_state_id,
            'partner_id': partner_id,
        })
        fact = gff_obj.browse(cursor, uid, fact_id)
        fact.write({
            'state': 'open',
            'type': 'out_invoice',
            'pending_state': consulta_state_id,
            'partner_id': partner_id,
        })
        fact.set_pending(consulta_state_id)
        cons_obj.write(cursor, uid, consulta_id, {
                       'resolucio': 'positiva'})
        cons_obj.close_case(cursor, uid, [consulta_id])

        fact = gff_obj.browse(cursor, uid, fact_id)
        fact3 = gff_obj.browse(cursor, uid, fact3_id)
        self.assertEqual(fact.pending_state.id, pobresa_state_id)
        self.assertEqual(fact3.pending_state.id, correcte_state_id)
