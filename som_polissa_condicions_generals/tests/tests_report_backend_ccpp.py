from destral import testing
from destral.transaction import Transaction


class TestReportBackendCCPP(testing.OOTestCase):
    def get_ref(self, module, ref):
        IrModel = self.openerp.pool.get("ir.model.data")
        return IrModel._get_obj(self.cursor, self.uid, module, ref).id

    def setUp(self):
        self.maxDiff = None
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.pol_obj = self.openerp.pool.get("giscedata.polissa")
        self.backend_obj = self.openerp.pool.get("report.backend.condicions.particulars")
        self.rpa_obj = self.openerp.pool.get("res.partner.address")
        self.gppcp_obj = self.openerp.pool.get("giscedata.polissa.potencia.contractada.periode")
        self.pricelist_obj = self.openerp.pool.get("product.pricelist")
        self.contract1_id = self.get_ref("giscedata_polissa", "polissa_0001")
        self.contract_20TD_id = self.get_ref("giscedata_polissa", "polissa_tarifa_018")
        self.contract_30TD_id = self.get_ref("giscedata_polissa", "polissa_tarifa_019")
        self.contract_61TD_id = self.get_ref("giscedata_polissa", "polissa_tarifa_020")

    def tearDown(self):
        self.txn.stop()

    def test_get_cups_data_ok(self):
        pol_20td = self.pol_obj.browse(self.cursor, self.uid, self.contract_20TD_id)

        result = self.backend_obj.get_cups_data(self.cursor, self.uid, pol_20td)

        self.assertEqual(result, {
            u'cnae': u'9820',
            u'cnae_des': u'Actividades de los hogares como productores de servicios para uso propio',  # noqa: E501
            u'country': u'Espa\xf1a',
            u'direccio': u'Pla\xe7a Mela Mutermilch 2 1 2 17001 (Girona)',
            u'distri': u'Agrolait',
            u'name': u'ES0021126262693495FV',
            u'provincia': u'Girona',
            u'ref_dist': u'',
            u'tensio': 127}
        )

    def test_get_titular_data_ok(self):
        pol_20td = self.pol_obj.browse(self.cursor, self.uid, self.contract_20TD_id)

        result = self.backend_obj.get_titular_data(self.cursor, self.uid, pol_20td, None)

        direccio_envio = self.rpa_obj.browse(self.cursor, self.uid, 2)
        direccio_titular = self.rpa_obj.browse(self.cursor, self.uid, 52)
        self.assertEqual(result, {
            u'city': u'Girona',
            u'city_envio': u'Bruxelles',
            u'client_name': u'GISCE',
            u'client_vat': u'B55129415',
            u'country': u'',
            u'country_envio': u'Belgium',
            u'diferent': True,
            u'direccio_envio': direccio_envio,
            u'direccio_titular': direccio_titular,
            u'email': u'',
            u'email_envio': u'info@openroad.be',
            u'mobile': u'',
            u'mobile_envio': u'',
            u'name_envio': u'Michel Schumacher',
            u'phone': u'',
            u'phone_envio': u'(+32) 2 123 456',
            u'sign_date': '',
            u'state': u'',
            u'state_envio': u'',
            u'street': u'Mela Mutermilch, 2 1 2',
            u'street_envio': u'Rue du flash 50',
            u'zip': u'17001',
            u'zip_envio': u'1000'}
        )

    def test_get_potencies_data_ok(self):
        pol_20td = self.pol_obj.browse(self.cursor, self.uid, self.contract_20TD_id)

        result = self.backend_obj.get_potencies_data(self.cursor, self.uid, pol_20td, None)

        p2 = self.gppcp_obj.browse(self.cursor, self.uid, 2)
        p3 = self.gppcp_obj.browse(self.cursor, self.uid, 3)
        self.assertEqual(result, {
            u'autoconsum': u'Sense Autoconsum',
            u'es_canvi_tecnic': False,
            u'periodes': [
                (1, p2), False, (2, p3),
                (4, False), (5, False), (6, False)],
            u'potencies': [p2, p3]}
        )

    def test_get_polissa_data_ok(self):
        pol_20td = self.pol_obj.browse(self.cursor, self.uid, self.contract_20TD_id)

        result = self.backend_obj.get_polissa_data(self.cursor, self.uid, pol_20td, context={})

        pricelist = self.pricelist_obj.browse(self.cursor, self.uid, 12)
        self.assertEqual(result, {
            u'auto': u'00',
            u'bank': False,
            u'contract_type': u'Anual',
            u'data_baixa': '2099-01-01',
            u'data_final': u'',
            u'data_inici': '2021-06-01',
            u'is_business': False,
            u'lead': False,
            u'modcon_pendent_indexada': False,
            u'modcon_pendent_periodes': False,
            u'mode_facturacio': u'atr',
            u'name': u'0018',
            u'periodes_energia': [u'P1', u'P2', u'P3'],
            u'periodes_potencia': [u'P1', u'P2'],
            u'potencia_max': 4.6,
            u'pricelist': pricelist,
            u'printable_iban': u'',
            u'state': u'esborrany',
            u'tarifa': u'2.0TD',
            u'tarifa_mostrar': u'TARIFAS ELECTRICIDAD VENDA',
            u'te_assignacio_gkwh': False}
        )

    def test_get_prices_data_ok(self):
        pol_20td = self.pol_obj.browse(self.cursor, self.uid, self.contract_20TD_id)

        result = self.backend_obj.get_prices_data(self.cursor, self.uid, pol_20td, context={})

        self.pricelist_obj.browse(self.cursor, self.uid, 12)
        self.assertEqual(result, {
            u'coeficient_k': False,
            u'coeficient_k_untaxed': 0.0,
            u'dict_preus_tp_energia': False,
            u'dict_preus_tp_potencia': False,
            u'mostra_indexada': False,
            u'pricelists': [{
                u'energy_prices': {
                    u'P1': 0.0,
                    u'P2': 0.0,
                    u'P3': 0.0},
                u'energy_prices_untaxed': {
                    u'P1': 0.0,
                    u'P2': 0.0,
                    u'P3': 0.0},
                u'generation_prices': {
                    u'P1': 0.0,
                    u'P2': 0.0,
                    u'P3': 0.0},
                u'generation_prices_untaxed': {
                    u'P1': 0.0,
                    u'P2': 0.0,
                    u'P3': 0.0},
                u'omie_mon_price_45': False,
                u'power_prices': {u'P1': 0.0, u'P2': 0.0},
                u'power_prices_untaxed': {u'P1': 0.0, u'P2': 0.0},
                u'price_auto': 0.01,
                u'price_auto_untaxed': 0.01,
                u'text_impostos': u' (IVA 21%, IE 3,8%)',
                u'text_vigencia': u''}]
        })
