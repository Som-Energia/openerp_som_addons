# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import mock


class WizardChangeToIndexadaAuvidiMultiBaseTests(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool
        self.wiz_obj = self.pool.get("wizard.change.to.indexada.auvidi.multi")
        self.polissa_obj = self.pool.get("giscedata.polissa")
        self.imd_obj = self.pool.get("ir.model.data")

    def tearDown(self):
        self.txn.stop()

    def get_model(self, model_name):
        return self.openerp.pool.get(model_name)

    def open_polissa(self, xml_id, mode_facturacio='atr', te_auvidi=False):
        polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", xml_id
        )[1]
        self.polissa_obj.write(self.cursor, self.uid, [polissa_id], {
            'mode_facturacio': mode_facturacio,
            'te_auvidi': te_auvidi,
        })

        self.polissa_obj.send_signal(self.cursor, self.uid, [polissa_id], ["validar", "contracte"])

        return polissa_id


class WizardChangeToIndexadaAuvidiMultiTests(WizardChangeToIndexadaAuvidiMultiBaseTests):

    def test__create_auvidi_pending_modcon__auvidi_True_index(self):
        polissa_id = self.open_polissa("polissa_tarifa_018", 'index')
        self.wiz_obj.create_auvidi_pending_modcon(self.cursor, self.uid, polissa_id, True)
        md = self.wiz_obj.get_last_pending_modcon(self.cursor, self.uid, polissa_id)
        self.assertEqual(md.te_auvidi, True)

    def test__create_auvidi_pending_modcon__auvidi_True_periods(self):
        polissa_id = self.open_polissa("polissa_tarifa_018")
        self.wiz_obj.create_auvidi_pending_modcon(self.cursor, self.uid, polissa_id, True)

        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(p.modcontractuals_ids[0].te_auvidi, True)

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test__inperiods_without_modcontoindex_to_auvidi(self, mocked_send_mail):
        # Periods without MODCON pending to indexed --> modcon pending Indexed + auvidi
        polissa_id = self.open_polissa("polissa_tarifa_018")

        context = {"active_id": polissa_id, "active_ids": [polissa_id]}
        wiz_id = self.wiz_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_obj.change_to_indexada_auvidi_multi(self.cursor, self.uid, [wiz_id], context)

        wiz = self.wiz_obj.browse(self.cursor, self.uid, wiz_id)
        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(p.modcontractuals_ids[0].te_auvidi, True)
        self.assertEqual(p.modcontractuals_ids[0].mode_facturacio, u'index')
        self.assertEqual(p.modcontractuals_ids[0].state, u'pendent')
        self.assertIn(u"Pòlisses que estan a periodes:", wiz.info)
        self.assertIn(u" - Creada modcon a indexada + auvidi: {}".format(p.name), wiz.info)

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test__inperiods_with_modcontoindex_to_auvidi(self, mocked_send_mail):
        # Periods with MODCON pending to indexed and auvidi --> don't do anything
        polissa_id = self.open_polissa("polissa_tarifa_018")

        context = {"active_id": polissa_id, "active_ids": [polissa_id]}
        wiz_id = self.wiz_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_obj.change_to_indexada_auvidi_multi(self.cursor, self.uid, [wiz_id], context)

        wiz_id = self.wiz_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_obj.change_to_indexada_auvidi_multi(self.cursor, self.uid, [wiz_id], context)

        wiz = self.wiz_obj.browse(self.cursor, self.uid, wiz_id)
        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(p.modcontractuals_ids[0].te_auvidi, True)
        self.assertEqual(p.modcontractuals_ids[0].mode_facturacio, u'index')
        self.assertEqual(p.modcontractuals_ids[0].state, u'pendent')
        self.assertIn(
            u"Pòlisses que estan a periodes i tenen modcon a indexada amb auvidi:", wiz.info)
        self.assertIn(u" - No fem res: {}".format(p.name), wiz.info)

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test__inperiods_with_modcontoindex_no_auvidi(self, mocked_send_mail):
        # Periods with MODCON pending to indexed --> modify the MODCON to add auvdi
        polissa_id = self.open_polissa("polissa_tarifa_018")

        context = {"active_id": polissa_id, "active_ids": [polissa_id]}
        wiz_id = self.wiz_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_obj.change_to_indexada_auvidi_multi(self.cursor, self.uid, [wiz_id], context)
        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.wiz_obj.set_auvidi(self.cursor, self.uid, p.modcontractuals_ids[0].id, False)

        wiz_id = self.wiz_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_obj.change_to_indexada_auvidi_multi(self.cursor, self.uid, [wiz_id], context)

        wiz = self.wiz_obj.browse(self.cursor, self.uid, wiz_id)
        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(p.modcontractuals_ids[0].te_auvidi, True)
        self.assertEqual(p.modcontractuals_ids[0].mode_facturacio, u'index')
        self.assertEqual(p.modcontractuals_ids[0].state, u'pendent')
        self.assertIn(u"Pòlisses que estan a periodes i tenen modcon a indexada:", wiz.info)
        self.assertIn(u" - Modcon modificada, afegit auvidi: {}".format(p.name), wiz.info)

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test__inindex_with_auvidi_without_modcon(self, mocked_send_mail):
        # Indexed and auvidiwith out MODCON to periods --> don't do anything
        polissa_id = self.open_polissa("polissa_tarifa_018", 'index', True)
        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        prev_modcons = len(p.modcontractuals_ids)

        context = {"active_id": polissa_id, "active_ids": [polissa_id]}
        wiz_id = self.wiz_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_obj.change_to_indexada_auvidi_multi(self.cursor, self.uid, [wiz_id], context)

        wiz = self.wiz_obj.browse(self.cursor, self.uid, wiz_id)
        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(p.te_auvidi, True)
        self.assertEqual(p.mode_facturacio, u'index')
        self.assertEqual(len(p.modcontractuals_ids), prev_modcons)
        self.assertIn(u"Pòlisses que estan a indexada amb auvidi:", wiz.info)
        self.assertIn(u" - No fem res: {}".format(p.name), wiz.info)

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test__inindex_without_auvidi_without_modcon(self, mocked_send_mail):
        # Indexed with out MODCON to periods --> create MODCON to auvidi
        polissa_id = self.open_polissa("polissa_tarifa_018", 'index', False)
        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        prev_modcons = len(p.modcontractuals_ids)

        context = {"active_id": polissa_id, "active_ids": [polissa_id]}
        wiz_id = self.wiz_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_obj.change_to_indexada_auvidi_multi(self.cursor, self.uid, [wiz_id], context)

        wiz = self.wiz_obj.browse(self.cursor, self.uid, wiz_id)
        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(p.modcontractuals_ids[0].te_auvidi, True)
        self.assertEqual(p.modcontractuals_ids[0].state, u'pendent')
        self.assertEqual(len(p.modcontractuals_ids), prev_modcons + 1)
        self.assertIn(u"Pòlisses que estan a indexada:", wiz.info)
        self.assertIn(u" - Creada modcon a auvidi: {}".format(p.name), wiz.info)

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test__inindex_with_modcon_to_period(self, mocked_send_mail):
        # Indexed with MODCON to periods --> error, cannot be done!
        polissa_id = self.open_polissa("polissa_tarifa_018", 'index', False)
        context = {"active_id": polissa_id, "active_ids": [polissa_id]}
        wiz_id = self.wiz_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_obj.change_to_indexada_auvidi_multi(self.cursor, self.uid, [wiz_id], context)
        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.wiz_obj.set_auvidi(self.cursor, self.uid, p.modcontractuals_ids[0].id, False)
        mod_obj = self.pool.get("giscedata.polissa.modcontractual")
        mod_obj.write(
            self.cursor, self.uid, p.modcontractuals_ids[0].id, {'mode_facturacio': 'atr'})
        prev_modcons = len(p.modcontractuals_ids)

        wiz_id = self.wiz_obj.create(self.cursor, self.uid, {}, context=context)
        self.wiz_obj.change_to_indexada_auvidi_multi(self.cursor, self.uid, [wiz_id], context)

        wiz = self.wiz_obj.browse(self.cursor, self.uid, wiz_id)
        p = self.polissa_obj.browse(self.cursor, self.uid, polissa_id)
        self.assertEqual(p.modcontractuals_ids[0].mode_facturacio, 'atr')
        self.assertEqual(p.modcontractuals_ids[0].state, u'pendent')
        self.assertEqual(len(p.modcontractuals_ids), prev_modcons)
        self.assertIn(
            u"ERROR Pòlisses que estan a indexada amb modcon pendent a periodes:", wiz.info)
        self.assertIn(u" - {}".format(p.name), wiz.info)
