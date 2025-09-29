# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import json


class TestsFacturacioBoSocial(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        pl_item_o = pool.get("product.pricelist.item")
        product_bs_id = self.get_object_id("som_polissa_soci", "bosocial_BS01")
        pl_version15_id = self.get_object_id("giscedata_tarifas_peajes_20150101", "boe_312_2014")
        pl_version16_id = self.get_object_id("giscedata_tarifas_peajes_20160101", "boe_302_2015")
        pl_version17_id = self.get_object_id("giscedata_tarifas_peajes_20170101", "boe_314_2016")
        pl_version18_id = self.get_object_id("giscedata_tarifas_peajes_20180101", "boe_314_2017")

        self.preu15 = 0.02
        self.preu16 = 0.01
        self.preu17 = 0.04
        self.preu18 = 0.03

        # Afegim una regla a la llista de preus base (versió del 2015): la del
        # producte de BS.
        pl_item_cv = {
            "product_id": product_bs_id,
            "price_version_id": pl_version15_id,
            "base_price": self.preu15,
            "base": -3,  # Pricelist item price
        }
        pl_item_o.create(cursor, uid, pl_item_cv)
        # El mateix d'abans pero per la versió del 2016
        pl_item_cv["price_version_id"] = pl_version16_id
        pl_item_cv["base_price"] = self.preu16
        pl_item_o.create(cursor, uid, pl_item_cv)
        # I per la del 2017
        pl_item_cv["price_version_id"] = pl_version17_id
        pl_item_cv["base_price"] = self.preu17
        pl_item_o.create(cursor, uid, pl_item_cv)
        # I per la del 2018
        pl_item_cv["price_version_id"] = pl_version18_id
        pl_item_cv["base_price"] = self.preu18
        pl_item_o.create(cursor, uid, pl_item_cv)

    def tearDown(self):
        self.txn.stop()

    def get_object_id(self, module, obj_ref):
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        irmd_o = pool.get("ir.model.data")
        object_id = irmd_o.get_object_reference(cursor, uid, module, obj_ref)[1]
        return object_id

    def test_add_bono_social_lines_case_a(self):
        """
        Comprova que s'afegeix una línia de bono social (BS01) a la factura.
        Cas A: la factura està integrament "dins" de la llista de preus::

            factura:       |-------------|
            l.preus:   |---------------------|

        @return:
        """
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        polissa_o = pool.get("giscedata.polissa")
        varconf_o = pool.get("res.config")
        wiz_o = pool.get("wizard.manual.invoice")
        linia_factura_o = pool.get("giscedata.facturacio.factura.linia")

        polissa_id = self.get_object_id("giscedata_polissa", "polissa_0001")
        journal_id = self.get_object_id("giscedata_facturacio", "facturacio_journal_energia")
        partner_id = self.get_object_id("base", "res_partner_agrolait")
        product_bs_id = self.get_object_id("som_polissa_soci", "bosocial_BS01")

        data_lectura_inici = "2016-02-02"
        data_lectura_final = "2016-03-03"

        # Configurem la pòlissa per tal de poder activar-la i facturar-la.
        polissa_wv = {"soci": partner_id, "data_ultima_lectura": data_lectura_inici}
        polissa_o.write(cursor, uid, polissa_id, polissa_wv)

        # Activem la pòlissa
        polissa_o.send_signal(cursor, uid, [polissa_id], ["validar", "contracte"])

        # Configurem algunes variables abans de facturar
        varconf_o.set(cursor, uid, "som_invoice_active_bo_social", 1)
        varconf_o.set(cursor, uid, "som_invoice_start_date_bo_social", "2016-01-01")

        # Facturem
        wiz_cv = {
            "polissa_id": polissa_id,
            "journal_id": journal_id,
            "date_start": data_lectura_inici,
            "date_end": data_lectura_final,
        }
        wiz_id = wiz_o.create(cursor, uid, wiz_cv)
        wiz_o.action_manual_invoice(cursor, uid, [wiz_id])
        wiz_o = wiz_o.browse(cursor, uid, wiz_id)

        # Busquem a les linies de la factura alguna que correspongui a la del BS
        invoice_id = json.loads(wiz_o.invoice_ids)[0]
        dmn = [("factura_id", "=", invoice_id), ("product_id", "=", product_bs_id)]
        linia_bs_ids = linia_factura_o.search(cursor, uid, dmn)

        # Ha de tenir només una línia de BS
        self.assertEqual(len(linia_bs_ids), 1)

        # Comprovem que el preu és l'adequat
        linia_factura_v = linia_factura_o.read(cursor, uid, linia_bs_ids[0], ["price_subtotal"])
        self.assertEqual(linia_factura_v["price_subtotal"], (30 + 1) * self.preu16)

    def test_add_bono_social_lines_case_b(self):
        """
        Comprova que s'afegeix una línia de bono social (BS01) a la factura.
        Cas B: hi ha un canvi de preus en mig del periode de facturació::

            factura:       |-------------|
            l.preus:   |----------|----------|

        @return:
        """
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        polissa_o = pool.get("giscedata.polissa")
        varconf_o = pool.get("res.config")
        wiz_o = pool.get("wizard.manual.invoice")
        linia_factura_o = pool.get("giscedata.facturacio.factura.linia")

        polissa_id = self.get_object_id("giscedata_polissa", "polissa_0001")
        journal_id = self.get_object_id("giscedata_facturacio", "facturacio_journal_energia")
        partner_id = self.get_object_id("base", "res_partner_agrolait")
        product_bs_id = self.get_object_id("som_polissa_soci", "bosocial_BS01")

        data_lectura_inici = "2016-02-02"
        data_lectura_final = "2017-01-31"

        # Configurem la pòlissa per tal de poder activar-la i facturar-la.
        polissa_wv = {
            "data_ultima_lectura": data_lectura_inici,
            "soci": partner_id,
            "data_baixa": data_lectura_final,
        }
        polissa_o.write(cursor, uid, polissa_id, polissa_wv)

        # Activem la pòlissa
        polissa_o.send_signal(cursor, uid, [polissa_id], ["validar", "contracte"])

        # Configurem algunes variables abans de facturar
        varconf_o.set(cursor, uid, "som_invoice_active_bo_social", 1)
        varconf_o.set(cursor, uid, "som_invoice_start_date_bo_social", "2016-01-01")

        # Facturem
        wiz_cv = {
            "polissa_id": polissa_id,
            "journal_id": journal_id,
            "date_start": data_lectura_inici,
            "date_end": data_lectura_final,
        }
        wiz_id = wiz_o.create(cursor, uid, wiz_cv)
        wiz_o.action_manual_invoice(cursor, uid, [wiz_id])
        wiz_o = wiz_o.browse(cursor, uid, wiz_id)

        # Busquem a les linies de la factura alguna que correspongui a la del BS
        invoice_id = json.loads(wiz_o.invoice_ids)[0]
        dmn = [("factura_id", "=", invoice_id), ("product_id", "=", product_bs_id)]
        linia_bs_ids = linia_factura_o.search(cursor, uid, dmn)

        # Ha de tenir exactament 2 línies de BS
        self.assertEqual(len(linia_bs_ids), 2)

        # Comprovem que el preu és l'adequat
        import_linies = {"2016": (333 + 1) * self.preu16, "2017": (30 + 1) * self.preu17}
        linia_factura_f = ["price_subtotal", "data_desde"]
        linia_factura_vs = linia_factura_o.read(cursor, uid, linia_bs_ids, linia_factura_f)
        for linia_factura_v in linia_factura_vs:
            year = linia_factura_v["data_desde"][:4]
            self.assertEqual(linia_factura_v["price_subtotal"], import_linies[year])

    def test_add_bono_social_lines_case_c(self):
        """
        Comprova que s'afegeix una línia de bono social (BS01) a la factura.
        Cas C: hi ha n canvis de preus en mig del periode de facturació::

            factura:       |-------------|
            l.preus:   |------|-------|------|

        En aquest cas 2 canvis de preus.
        @return:
        """
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        polissa_o = pool.get("giscedata.polissa")
        varconf_o = pool.get("res.config")
        lectura_o = pool.get("giscedata.lectures.lectura")
        wiz_o = pool.get("wizard.manual.invoice")
        linia_factura_o = pool.get("giscedata.facturacio.factura.linia")

        polissa_id = self.get_object_id("giscedata_polissa", "polissa_0001")
        journal_id = self.get_object_id("giscedata_facturacio", "facturacio_journal_energia")
        partner_id = self.get_object_id("base", "res_partner_agrolait")
        lectura_id = self.get_object_id("giscedata_facturacio", "lectura_0006")
        product_bs_id = self.get_object_id("som_polissa_soci", "bosocial_BS01")

        data_lectura_inici = "2016-02-02"
        data_lectura_final = "2018-01-31"

        # Configurem la pòlissa per tal de poder activar-la i facturar-la.
        polissa_wv = {
            "data_ultima_lectura": data_lectura_inici,
            "soci": partner_id,
            "data_baixa": data_lectura_final,
        }
        polissa_o.write(cursor, uid, polissa_id, polissa_wv)

        # Activem la pòlissa
        polissa_o.send_signal(cursor, uid, [polissa_id], ["validar", "contracte"])

        # Afegim una lectura per forçar la facturació a tres versions de la
        # llista de preus
        lectura_wv = {"name": data_lectura_final, "lectura": 20}
        lectura_o.copy(cursor, uid, lectura_id, lectura_wv)

        # Configurem algunes variables abans de facturar
        varconf_o.set(cursor, uid, "som_invoice_active_bo_social", 1)
        varconf_o.set(cursor, uid, "som_invoice_start_date_bo_social", "2016-01-01")

        # Facturem
        wiz_cv = {
            "polissa_id": polissa_id,
            "journal_id": journal_id,
            "date_start": data_lectura_inici,
            "date_end": data_lectura_final,
        }
        wiz_id = wiz_o.create(cursor, uid, wiz_cv)
        wiz_o.action_manual_invoice(cursor, uid, [wiz_id])
        wiz_o = wiz_o.browse(cursor, uid, wiz_id)

        # Busquem a les linies de la factura alguna que correspongui a la del BS
        invoice_id = json.loads(wiz_o.invoice_ids)[0]
        dmn = [("factura_id", "=", invoice_id), ("product_id", "=", product_bs_id)]
        linia_bs_ids = linia_factura_o.search(cursor, uid, dmn)

        # Ha de tenir exactament 3 línies de BS
        self.assertEqual(len(linia_bs_ids), 3)

        # Comprovem que el preu és l'adequat
        import_linies = {
            "2016": (333 + 1) * self.preu16,
            "2017": (364 + 1) * self.preu17,
            "2018": (30 + 1) * self.preu18,
        }
        linia_factura_f = ["price_subtotal", "data_desde"]
        linia_factura_vs = linia_factura_o.read(cursor, uid, linia_bs_ids, linia_factura_f)
        for linia_factura_v in linia_factura_vs:
            year = linia_factura_v["data_desde"][:4]
            self.assertAlmostEqual(linia_factura_v["price_subtotal"], import_linies[year])

    def test_add_bono_social_lines_case_d(self):
        """
        Comprova que s'afegeix una línia de bono social (BS01) a la factura.
        Cas D: com el cas A però la versió no té data final::

            factura:       |-------------|
            l.preus:   |-------------------...

        @return:
        """
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        polissa_o = pool.get("giscedata.polissa")
        varconf_o = pool.get("res.config")
        wiz_o = pool.get("wizard.manual.invoice")
        linia_factura_o = pool.get("giscedata.facturacio.factura.linia")
        pl_version_o = pool.get("product.pricelist.version")

        polissa_id = self.get_object_id("giscedata_polissa", "polissa_0001")
        journal_id = self.get_object_id("giscedata_facturacio", "facturacio_journal_energia")
        partner_id = self.get_object_id("base", "res_partner_agrolait")
        pl_version16_id = self.get_object_id("giscedata_tarifas_peajes_20160101", "boe_302_2015")
        pl_version17_id = self.get_object_id("giscedata_tarifas_peajes_20170101", "boe_314_2016")
        pl_version18_id = self.get_object_id("giscedata_tarifas_peajes_20180101", "boe_314_2017")
        product_bs_id = self.get_object_id("som_polissa_soci", "bosocial_BS01")

        data_lectura_inici = "2016-02-02"
        data_lectura_final = "2016-03-03"

        # Desactivem les versions posteriors a la del 2016
        pl_version_wv = {"active": False}
        pl_version_post16_ids = [pl_version17_id, pl_version18_id]
        pl_version_o.write(cursor, uid, pl_version_post16_ids, pl_version_wv)
        # I forcem que la versión de preus del 2016 no tingui final
        pl_version_wv = {"date_end": False}
        pl_version_o.write(cursor, uid, pl_version16_id, pl_version_wv)

        # Configurem la pòlissa per tal de poder activar-la i facturar-la.
        polissa_wv = {
            "data_ultima_lectura": data_lectura_inici,
            "soci": partner_id,
        }
        polissa_o.write(cursor, uid, polissa_id, polissa_wv)

        # Activem la pòlissa
        polissa_o.send_signal(cursor, uid, [polissa_id], ["validar", "contracte"])

        # Configurem algunes variables abans de facturar
        varconf_o.set(cursor, uid, "som_invoice_active_bo_social", 1)
        varconf_o.set(cursor, uid, "som_invoice_start_date_bo_social", "2016-01-01")

        # Facturem
        wiz_cv = {
            "polissa_id": polissa_id,
            "journal_id": journal_id,
            "date_start": data_lectura_inici,
            "date_end": data_lectura_final,
        }
        wiz_id = wiz_o.create(cursor, uid, wiz_cv)
        wiz_o.action_manual_invoice(cursor, uid, [wiz_id])
        wiz_o = wiz_o.browse(cursor, uid, wiz_id)

        # Busquem a les linies de la factura alguna que correspongui a la del BS
        invoice_id = json.loads(wiz_o.invoice_ids)[0]
        dmn = [("factura_id", "=", invoice_id), ("product_id", "=", product_bs_id)]
        linia_bs_ids = linia_factura_o.search(cursor, uid, dmn)

        # Ha de tenir exactament 3 línies de BS
        self.assertEqual(len(linia_bs_ids), 1)

        # No cal testejar l'import de la linia ja que ja ho fa el cas A

    def test_add_bono_social_lines_case_e(self):
        """
        Comprova que s'afegeix una línia de bono social (BS01) a la factura.
        Cas B: hi ha un canvi de preus en mig del periode de facturació::

            factura:       |-------------|
            l.preus:   |----------|----------...

        @return:
        """
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        polissa_o = pool.get("giscedata.polissa")
        varconf_o = pool.get("res.config")
        wiz_o = pool.get("wizard.manual.invoice")
        pl_version_o = pool.get("product.pricelist.version")
        linia_factura_o = pool.get("giscedata.facturacio.factura.linia")

        polissa_id = self.get_object_id("giscedata_polissa", "polissa_0001")
        journal_id = self.get_object_id("giscedata_facturacio", "facturacio_journal_energia")
        partner_id = self.get_object_id("base", "res_partner_agrolait")
        product_bs_id = self.get_object_id("som_polissa_soci", "bosocial_BS01")
        pl_version17_id = self.get_object_id("giscedata_tarifas_peajes_20170101", "boe_314_2016")
        pl_version18_id = self.get_object_id("giscedata_tarifas_peajes_20180101", "boe_314_2017")

        data_lectura_inici = "2016-02-02"
        data_lectura_final = "2017-01-31"

        # Desactivem la versió del 2018
        pl_version_wv = {"active": False}
        pl_version_o.write(cursor, uid, pl_version18_id, pl_version_wv)
        # I forcem que la versión de preus del 2017 no tingui final
        pl_version_wv = {"date_end": False}
        pl_version_o.write(cursor, uid, pl_version17_id, pl_version_wv)

        # Configurem la pòlissa per tal de poder activar-la i facturar-la.
        polissa_wv = {
            "data_ultima_lectura": data_lectura_inici,
            "soci": partner_id,
            "data_baixa": data_lectura_final,
        }
        polissa_o.write(cursor, uid, polissa_id, polissa_wv)

        # Activem la pòlissa
        polissa_o.send_signal(cursor, uid, [polissa_id], ["validar", "contracte"])

        # Configurem algunes variables abans de facturar
        varconf_o.set(cursor, uid, "som_invoice_active_bo_social", 1)
        varconf_o.set(cursor, uid, "som_invoice_start_date_bo_social", "2016-01-01")

        # Facturem
        wiz_cv = {
            "polissa_id": polissa_id,
            "journal_id": journal_id,
            "date_start": data_lectura_inici,
            "date_end": data_lectura_final,
        }
        wiz_id = wiz_o.create(cursor, uid, wiz_cv)
        wiz_o.action_manual_invoice(cursor, uid, [wiz_id])
        wiz_o = wiz_o.browse(cursor, uid, wiz_id)

        # Busquem a les linies de la factura alguna que correspongui a la del BS
        invoice_id = json.loads(wiz_o.invoice_ids)[0]
        dmn = [("factura_id", "=", invoice_id), ("product_id", "=", product_bs_id)]
        linia_bs_ids = linia_factura_o.search(cursor, uid, dmn)

        # Ha de tenir exactament 2 línies de BS
        self.assertEqual(len(linia_bs_ids), 2)

        # No cal testejar l'import de la linia ja que ja ho fa el cas B

    def test_add_bono_social_lines_case_f(self):
        """
        Comprova que s'afegeix una línia de bono social (BS01) a la factura.
        Cas F: el bo social deixa de ser d'aplicació amb la segona llista de preus

            factura:       |--------------|
            l.preus:   |----------Fi BS|

        @return:
        """
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        polissa_o = pool.get("giscedata.polissa")
        varconf_o = pool.get("res.config")
        wiz_o = pool.get("wizard.manual.invoice")
        pl_version_o = pool.get("product.pricelist.version")
        linia_factura_o = pool.get("giscedata.facturacio.factura.linia")

        polissa_id = self.get_object_id("giscedata_polissa", "polissa_0001")
        journal_id = self.get_object_id("giscedata_facturacio", "facturacio_journal_energia")
        partner_id = self.get_object_id("base", "res_partner_agrolait")
        product_bs_id = self.get_object_id("som_polissa_soci", "bosocial_BS01")
        pl_version16_id = self.get_object_id("giscedata_tarifas_peajes_20160101", "boe_302_2015")
        data_lectura_inici = "2016-02-02"
        data_lectura_final = "2017-01-31"

        end_plv_16 = pl_version_o.read(cursor, uid, pl_version16_id, ["date_end"])["date_end"]

        # Configurem la pòlissa per tal de poder activar-la i facturar-la.
        polissa_wv = {
            "data_ultima_lectura": data_lectura_inici,
            "soci": partner_id,
            "data_baixa": data_lectura_final,
        }
        polissa_o.write(cursor, uid, polissa_id, polissa_wv)

        # Activem la pòlissa
        polissa_o.send_signal(cursor, uid, [polissa_id], ["validar", "contracte"])

        # Configurem algunes variables abans de facturar
        varconf_o.set(cursor, uid, "som_invoice_active_bo_social", 1)
        varconf_o.set(cursor, uid, "som_invoice_start_date_bo_social", "2016-01-01")
        varconf_o.set(cursor, uid, "som_invoice_end_date_bo_social", end_plv_16)

        # Facturem
        wiz_cv = {
            "polissa_id": polissa_id,
            "journal_id": journal_id,
            "date_start": data_lectura_inici,
            "date_end": data_lectura_final,
        }
        wiz_id = wiz_o.create(cursor, uid, wiz_cv)
        wiz_o.action_manual_invoice(cursor, uid, [wiz_id])
        wiz_o = wiz_o.browse(cursor, uid, wiz_id)

        # Busquem a les linies de la factura alguna que correspongui a la del BS
        invoice_id = json.loads(wiz_o.invoice_ids)[0]
        dmn = [("factura_id", "=", invoice_id), ("product_id", "=", product_bs_id)]
        linia_bs_ids = linia_factura_o.search(cursor, uid, dmn)

        # Ha de tenir exactament 2 línies de BS
        self.assertEqual(len(linia_bs_ids), 1)

        # No cal testejar l'import de la linia ja que ja ho fa el cas B
        # Comprovem que el preu és l'adequat
        import_linia = (333 + 1) * self.preu16
        linia_factura_f = ["price_subtotal", "data_desde"]
        linia_factura_v = linia_factura_o.read(cursor, uid, linia_bs_ids[0], linia_factura_f)
        self.assertEqual(linia_factura_v["price_subtotal"], import_linia)

    def test_add_bono_social_lines_case_g(self):
        """
        Comprova que s'afegeix una línia de bono social (BS01) a la factura.
        Cas F: el bo social deixa de ser d'aplicació amb la segona llista de preus

            factura:                 |--------------|
            l.preus:   |-----Fi BS|

        @return:
        """
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        polissa_o = pool.get("giscedata.polissa")
        varconf_o = pool.get("res.config")
        wiz_o = pool.get("wizard.manual.invoice")
        pl_version_o = pool.get("product.pricelist.version")
        linia_factura_o = pool.get("giscedata.facturacio.factura.linia")

        polissa_id = self.get_object_id("giscedata_polissa", "polissa_0001")
        journal_id = self.get_object_id("giscedata_facturacio", "facturacio_journal_energia")
        partner_id = self.get_object_id("base", "res_partner_agrolait")
        product_bs_id = self.get_object_id("som_polissa_soci", "bosocial_BS01")
        pl_version16_id = self.get_object_id("giscedata_tarifas_peajes_20160101", "boe_302_2015")
        data_lectura_inici = "2016-02-02"
        data_lectura_final = "2017-01-31"

        pl_version_o.read(cursor, uid, pl_version16_id, ["date_end"])["date_end"]

        # Configurem la pòlissa per tal de poder activar-la i facturar-la.
        polissa_wv = {
            "data_ultima_lectura": data_lectura_inici,
            "soci": partner_id,
            "data_baixa": data_lectura_final,
        }
        polissa_o.write(cursor, uid, polissa_id, polissa_wv)

        # Activem la pòlissa
        polissa_o.send_signal(cursor, uid, [polissa_id], ["validar", "contracte"])

        # Configurem algunes variables abans de facturar
        varconf_o.set(cursor, uid, "som_invoice_active_bo_social", 1)
        varconf_o.set(cursor, uid, "som_invoice_start_date_bo_social", "2014-01-01")
        varconf_o.set(cursor, uid, "som_invoice_end_date_bo_social", "2015-01-01")

        # Facturem
        wiz_cv = {
            "polissa_id": polissa_id,
            "journal_id": journal_id,
            "date_start": data_lectura_inici,
            "date_end": data_lectura_final,
        }
        wiz_id = wiz_o.create(cursor, uid, wiz_cv)
        wiz_o.action_manual_invoice(cursor, uid, [wiz_id])
        wiz_o = wiz_o.browse(cursor, uid, wiz_id)

        # Busquem a les linies de la factura alguna que correspongui a la del BS
        invoice_id = json.loads(wiz_o.invoice_ids)[0]
        dmn = [("factura_id", "=", invoice_id), ("product_id", "=", product_bs_id)]
        linia_bs_ids = linia_factura_o.search(cursor, uid, dmn)

        # Ha de tenir exactament 2 línies de BS
        self.assertEqual(len(linia_bs_ids), 0)
