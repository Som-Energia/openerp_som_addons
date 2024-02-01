from destral import testing
from destral.transaction import Transaction
import mock


class TestGisceDataCups(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.pol_obj = self.model("giscedata.polissa")
        self.contract1_id = self.get_ref("giscedata_polissa", "polissa_0001")
        self.contract_20TD_id = self.get_ref("giscedata_polissa", "polissa_tarifa_018")
        self.contract_30TD_id = self.get_ref("giscedata_polissa", "polissa_tarifa_019")
        self.contract_61TD_id = self.get_ref("giscedata_polissa", "polissa_tarifa_020")

    def tearDown(self):
        self.txn.stop()

    def get_ref(self, module, ref):
        IrModel = self.model("ir.model.data")
        return IrModel._get_obj(self.cursor, self.uid, module, ref).id

    @mock.patch(
        "giscedata_facturacio_comer.giscedata_facturacio_report_v2.GiscedataFacturacioFacturaReportV2.get_grafica_historic_consum_14_mesos"
    )
    def test__get_consum_anual_backend_gisce__lessThan12(self, mock_function):
        mock_function.return_value = {
            u"historic": {
                u"average_consumption": u"23,35",
                u"average_cost": u"4,95",
                u"consumption": u"9.947,00",
                u"days": 426,
                u"end_date": u"15/08/2023",
                u"init_date": u"16/06/2022",
                u"invoiced": u"2.109,66",
                u"months": 14,
                u"year_consumption": u"9.432,00",
            },
            u"historic_js": [
                {u"P1": u"132,00", u"P2": u"92,00", u"P3": u"194,00", u"mes": u"2023/07"},
                {u"P1": u"183,00", u"P2": u"99,00", u"P3": u"256,00", u"mes": u"2023/08"},
            ],
        }

        result = self.pol_obj.get_consum_anual_backend_gisce(
            self.cursor, self.uid, self.contract_20TD_id
        )

        self.assertEqual(result, False)

    @mock.patch(
        "giscedata_facturacio_comer.giscedata_facturacio_report_v2.GiscedataFacturacioFacturaReportV2.get_grafica_historic_consum_14_mesos"
    )
    def test__get_consum_anual_backend_gisce__noInvoices(self, mock_function):
        mock_function.return_value = {}

        result = self.pol_obj.get_consum_anual_backend_gisce(
            self.cursor, self.uid, self.contract_20TD_id
        )

        self.assertEqual(result, False)

    @mock.patch(
        "giscedata_facturacio_comer.giscedata_facturacio_report_v2.GiscedataFacturacioFacturaReportV2.get_grafica_historic_consum_14_mesos"
    )
    def test__get_consum_anual_backend_gisce__moreThan12(self, mock_function):
        mock_function.return_value = {
            u"historic": {
                u"average_consumption": u"23,35",
                u"average_cost": u"4,95",
                u"consumption": u"9.947,00",
                u"days": 426,
                u"end_date": u"15/08/2023",
                u"init_date": u"16/06/2022",
                u"invoiced": u"2.109,66",
                u"months": 14,
                u"year_consumption": u"9.432,00",
            },
            u"historic_js": [
                {u"P1": u"176,00", u"P2": u"122,00", u"P3": u"217,00", u"mes": u"2022/07"},
                {u"P1": u"203,00", u"P2": u"179,00", u"P3": u"411,00", u"mes": u"2022/08"},
                {u"P1": u"84,00", u"P2": u"65,00", u"P3": u"155,00", u"mes": u"2022/09"},
                {u"P1": u"107,00", u"P2": u"63,00", u"P3": u"247,00", u"mes": u"2022/10"},
                {u"P1": u"146,00", u"P2": u"121,00", u"P3": u"245,00", u"mes": u"2022/11"},
                {u"P1": u"356,00", u"P2": u"405,00", u"P3": u"750,00", u"mes": u"2022/12"},
                {u"P1": u"269,00", u"P2": u"330,00", u"P3": u"697,00", u"mes": u"2023/01"},
                {u"P1": u"414,00", u"P2": u"430,00", u"P3": u"564,00", u"mes": u"2023/02"},
                {u"P1": u"235,00", u"P2": u"220,00", u"P3": u"474,00", u"mes": u"2023/03"},
                {u"P1": u"145,00", u"P2": u"114,00", u"P3": u"327,00", u"mes": u"2023/04"},
                {u"P1": u"93,00", u"P2": u"67,00", u"P3": u"234,00", u"mes": u"2023/05"},
                {u"P1": u"88,00", u"P2": u"66,00", u"P3": u"172,00", u"mes": u"2023/06"},
                {u"P1": u"132,00", u"P2": u"92,00", u"P3": u"194,00", u"mes": u"2023/07"},
                {u"P1": u"183,00", u"P2": u"99,00", u"P3": u"256,00", u"mes": u"2023/08"},
            ],
        }

        result = self.pol_obj.get_consum_anual_backend_gisce(
            self.cursor, self.uid, self.contract1_id
        )

        self.assertEqual(result, {"P2": 2033, "P3": 4235, "P1": 2254, "P6": 0, "P4": 0, "P5": 0})

    @mock.patch(
        "giscedata_facturacio_comer.giscedata_facturacio_report_v2.GiscedataFacturacioFacturaReportV2.get_grafica_historic_consum_14_mesos"
    )
    def test__get_consum_prorrageig_cnmc__lessThan2(self, mock_function):
        mock_function.return_value = {
            u"historic": {
                u"average_consumption": u"23,35",
                u"average_cost": u"4,95",
                u"consumption": u"9.947,00",
                u"days": 426,
                u"end_date": u"15/08/2023",
                u"init_date": u"16/06/2022",
                u"invoiced": u"2.109,66",
                u"months": 14,
                u"year_consumption": u"9.432,00",
            },
            u"historic_js": [
                {u"P1": u"132,00", u"P2": u"92,00", u"P3": u"194,00", u"mes": u"2023/07"},
                {u"P1": u"183,00", u"P2": u"99,00", u"P3": u"256,00", u"mes": u"2023/08"},
            ],
        }

        result = self.pol_obj.get_consum_prorrageig_cnmc(
            self.cursor, self.uid, self.contract_20TD_id
        )

        self.assertEqual(result, False)

    @mock.patch(
        "giscedata_facturacio_comer.giscedata_facturacio_report_v2.GiscedataFacturacioFacturaReportV2.get_grafica_historic_consum_14_mesos"
    )
    def test__get_consum_prorrageig_cnmc__noInvoices(self, mock_function):
        mock_function.return_value = {}

        result = self.pol_obj.get_consum_prorrageig_cnmc(
            self.cursor, self.uid, self.contract_20TD_id
        )

        self.assertEqual(result, False)

    @mock.patch(
        "giscedata_facturacio_comer.giscedata_facturacio_report_v2.GiscedataFacturacioFacturaReportV2.get_grafica_historic_consum_14_mesos"
    )
    def test__get_consum_prorrageig_cnmc__moreThan2(self, mock_function):
        mock_function.return_value = {
            u"historic": {
                u"average_consumption": u"23,35",
                u"average_cost": u"4,95",
                u"consumption": u"9.947,00",
                u"days": 426,
                u"end_date": u"15/08/2023",
                u"init_date": u"16/06/2022",
                u"invoiced": u"2.109,66",
                u"months": 14,
                u"year_consumption": u"9.432,00",
            },
            u"historic_js": [
                {u"P1": u"176,00", u"P2": u"122,00", u"P3": u"217,00", u"mes": u"2022/07"},
                {u"P1": u"203,00", u"P2": u"179,00", u"P3": u"411,00", u"mes": u"2022/08"},
                {u"P1": u"414,00", u"P2": u"430,00", u"P3": u"564,00", u"mes": u"2023/02"},
                {u"P1": u"235,00", u"P2": u"220,00", u"P3": u"474,00", u"mes": u"2023/03"},
                {u"P1": u"145,00", u"P2": u"114,00", u"P3": u"327,00", u"mes": u"2023/04"},
                {u"P1": u"93,00", u"P2": u"67,00", u"P3": u"234,00", u"mes": u"2023/05"},
                {u"P1": u"88,00", u"P2": u"66,00", u"P3": u"172,00", u"mes": u"2023/06"},
            ],
        }

        result = self.pol_obj.get_consum_prorrageig_cnmc(self.cursor, self.uid, self.contract1_id)

        self.assertEqual(result, {"P2": 2050, "P3": 4105, "P1": 2317, "P6": 0, "P4": 0, "P5": 0})

    def test__get_consum_anual_estadistic_som__periods_20TD(self):
        result = self.pol_obj.get_consum_anual_estadistic_som(
            self.cursor, self.uid, self.contract_20TD_id, {"periods": True}
        )

        self.assertEqual(result, {"P1": 722, "P2": 660, "P3": 1117, "P4": 0, "P5": 0, "P6": 0})

    def test__get_consum_anual_estadistic_som__periods_30TD(self):
        result = self.pol_obj.get_consum_anual_estadistic_som(
            self.cursor, self.uid, self.contract_30TD_id, {"periods": True}
        )

        self.assertEqual(
            result, {"P1": 6600, "P2": 1650, "P3": 1650, "P4": 1650, "P5": 1650, "P6": 3300}
        )

    def test__get_consum_anual_estadistic_som__periods_61TD(self):
        result = self.pol_obj.get_consum_anual_estadistic_som(
            self.cursor, self.uid, self.contract_61TD_id, {"periods": True}
        )

        self.assertEqual(result, False)

    def test__get_consum_anual_estadistic_som__agreggated_20TD(self):
        result = self.pol_obj.get_consum_anual_estadistic_som(
            self.cursor, self.uid, self.contract_20TD_id, {"periods": False}
        )

        self.assertEqual(result, 2500)

    def test__get_consum_anual_estadistic_som__agreggated_30TD(self):
        result = self.pol_obj.get_consum_anual_estadistic_som(
            self.cursor, self.uid, self.contract_30TD_id, {"periods": False}
        )

        self.assertEqual(result, 16500)

    def test__get_consum_anual_estadistic_som__agreggated_61TD(self):
        result = self.pol_obj.get_consum_anual_estadistic_som(
            self.cursor, self.uid, self.contract_61TD_id, {"periods": False}
        )

        self.assertEqual(result, False)
