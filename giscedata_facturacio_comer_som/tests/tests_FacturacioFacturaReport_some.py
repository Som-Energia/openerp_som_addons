# -*- coding: utf-8 -*-

import mock
import unittest
from destral import testing
from destral.transaction import Transaction
from yamlns import namespace as ns
from yamlns.testutils import assertNsEqual
from datetime import datetime
from .. import giscedata_facturacio_report


class Tests_FacturacioFacturaReport_base(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.r_obj = self.model("giscedata.facturacio.factura.report")
        self.factura_obj = self.model("giscedata.facturacio.factura")
        self.polissa_obj = self.model("giscedata.polissa")
        self.partner_obj = self.model("res.partner")
        self.par_add_obj = self.model("res.partner.address")
        self.linia_f_obj = self.model("giscedata.facturacio.factura.linia")
        self.partner_bank_obj = self.model("res.partner.bank")
        self.payment_type_obj = self.model("payment.type")

    def tearDown(self):
        self.txn.stop()

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_fixture(self, model, reference):
        imd_obj = self.model("ir.model.data")
        return imd_obj.get_object_reference(self.txn.cursor, self.txn.user, model, reference)[1]

    def bf(self, f_id):
        return self.factura_obj.browse(self.cursor, self.uid, f_id)

    def bfp(self, f_id):
        fac = self.factura_obj.browse(self.cursor, self.uid, f_id)
        pol = self.polissa_obj.browse(self.cursor, self.uid, fac.polissa_id.id)
        return {"fact": fac, "pol": pol}

    def setup_langs(self):
        lang_obj = self.model("res.lang")
        lang_obj.create(self.cursor, self.uid, {"name": "cas", "code": "es_ES"})
        lang_obj.create(self.cursor, self.uid, {"name": "cat", "code": "ca_ES"})

    def assertYamlfy(self, result):
        self.assertTrue(len(ns.loads(ns(result).dump()).keys()) >= 0)


class Tests_FacturacioFacturaReport_fill_and_find(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_auvi_data"
    )
    def test__get_report_data__simple_list(self, get_auvi_data_mock_function):
        f_id1 = self.get_fixture("giscedata_facturacio", "factura_0001")
        f_id2 = self.get_fixture("giscedata_facturacio", "factura_0002")
        ctxt = {"allow_list": ["logo", "company"], "not_testing_old_polissa": True}
        get_auvi_data_mock_function.return_value = False

        result = self.r_obj.get_report_data(
            self.cursor, self.uid, [self.bf(f_id1), self.bf(f_id2)], ctxt
        )

        self.assertTrue(f_id1 in result.keys())
        self.assertTrue("logo" in result[f_id1])
        self.assertTrue("company" in result[f_id1])

        self.assertTrue(f_id2 in result.keys())
        self.assertTrue("logo" in result[f_id2])
        self.assertTrue("company" in result[f_id2])

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_auvi_data"
    )
    def test__get_report_data__cross_test_1_sample(self, get_auvi_data_mock_function):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        ctxt = {"allow_list": ["logo", "company"], "not_testing_old_polissa": True}
        get_auvi_data_mock_function.return_value = False

        result1 = self.r_obj.get_components_data(self.cursor, self.uid, [f_id], ctxt)
        result2 = self.r_obj.get_report_data(self.cursor, self.uid, [self.bf(f_id)], ctxt)

        assertNsEqual(self, result1, result2)

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_auvi_data"
    )
    def test__get_report_data__cross_test_more_sample(self, get_auvi_data_mock_function):
        f_id1 = self.get_fixture("giscedata_facturacio", "factura_0001")
        f_id2 = self.get_fixture("giscedata_facturacio", "factura_0002")
        ctxt = {"allow_list": ["logo", "company"], "not_testing_old_polissa": True}
        get_auvi_data_mock_function.return_value = False

        result1 = self.r_obj.get_components_data(self.cursor, self.uid, [f_id1, f_id2], ctxt)
        result2 = self.r_obj.get_report_data(
            self.cursor, self.uid, [self.bf(f_id1), self.bf(f_id2)], ctxt
        )

        assertNsEqual(self, result1, result2)

    def test__find_all_components_data__detect_some_of_them(self):
        methods = self.r_obj.find_all_components_data()

        self.assertTrue("logo" in methods.keys())
        self.assertEquals(methods["logo"].__name__, "get_component_logo_data")
        self.assertEquals(methods["logo"].im_class.__name__, "giscedata.facturacio.factura.report")

        self.assertTrue("company" in methods.keys())
        self.assertEquals(methods["company"].__name__, "get_component_company_data")
        self.assertEquals(
            methods["company"].im_class.__name__, "giscedata.facturacio.factura.report"
        )

        for name, method in methods.items():
            self.assertEquals(method.im_class.__name__, "giscedata.facturacio.factura.report")

    @mock.patch.object(giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "cleanup_data")
    def test__fill_all_components_data__test_some_of_them(self, cleanup_data_function_mock):

        cleanup_data_function_mock.return_value = False

        def returnA(fac, pol):
            return {"A": "resultA", "Z": "resultZ"}

        def returnB(fac, pol):
            return {"B": "resultB"}

        def returnC(fac, pol):
            return {"C": [1, 2, 3, 4, 5, 6, 7, 42]}

        methods = {
            "MethodA": returnA,
            "MethodB": returnB,
            "MethodC": returnC,
        }

        result = self.r_obj.fill_all_components_data(methods, None, None, None)
        assertNsEqual(
            self,
            result,
            """
        MethodA:
          A: resultA
          Z: resultZ
        MethodB:
          B: resultB
        MethodC:
          C:
            - 1
            - 2
            - 3
            - 4
            - 5
            - 6
            - 7
            - 42
        """,
        )


class Tests_FacturacioFacturaReport_logo_component(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_auvi_data"
    )
    def test__som_report_comp_logo__no_soci(self, get_auvi_data_mock_function):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        get_auvi_data_mock_function.return_value = False

        result = self.r_obj.get_component_logo_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {"logo": "logo_som2.png", "has_agreement_partner": False, "has_auvi": False},
        )

    @unittest.skip(reason="WIP using mock")
    @mock.patch("som_polissa_soci.giscedata_polissa.GiscedataPolissa")
    def test__som_report_comp_logo__energetica_mock(self, patch):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.get_fixture("giscedata_polissa", "polissa_0001")

        print "+-" * 50  # noqa: E999
        print f.polissa_id  # noqa: F821
        print f.polissa_id.soci  # noqa: F821
        print f.polissa_id.id  # noqa: F821

        p = self.partner_obj.browse(self.cursor, self.uid, 23)
        self.partner_obj.write(self.cursor, self.uid, p.id, {"ref": "S019753"})
        print "*" * 50
        print p
        print p.ref

        with patch("soci") as polissa:
            polissa.return_value = "S019753"

            print "*" * 50
            print f.polissa_id.soci  # noqa: F821

            result = self.r_obj.get_component_logo_data(**self.bfp(f_id))
            self.assertYamlfy(result)
            self.assertEquals(
                result,
                {
                    "logo": "logo_som2.png",
                    "has_agreement_partner": True,
                    "logo_agreement_partner": "logo_S019753.png",
                },
            )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_auvi_data"
    )
    def test__som_report_comp_logo__no_energetica(self, get_auvi_data_mock_function):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        get_auvi_data_mock_function.return_value = False

        p_id = 23
        self.partner_obj.write(self.cursor, self.uid, p_id, {"ref": "S12345"})
        self.polissa_obj.write(self.cursor, self.uid, f.polissa_id.id, {"soci": p_id})

        result = self.r_obj.get_component_logo_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {"logo": "logo_som2.png", "has_agreement_partner": False, "has_auvi": False})

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_auvi_data"
    )
    def test__som_report_comp_logo__energetica(self, get_auvi_data_mock_function):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        get_auvi_data_mock_function.return_value = False

        p_id = 23
        self.partner_obj.write(self.cursor, self.uid, p_id, {"ref": "S019753"})
        self.polissa_obj.write(self.cursor, self.uid, f.polissa_id.id, {"soci": p_id})

        result = self.r_obj.get_component_logo_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "logo": "logo_som2.png",
                "has_agreement_partner": True,
                "logo_agreement_partner": "logo_S019753.png",
                "has_auvi": False,
            },
        )


class Tests_FacturacioFacturaReport_company_component(Tests_FacturacioFacturaReport_base):
    def test__som_report_comp_company__base(self):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_company_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "cif": u"A31896889",
                "city": u"Gerompont",
                "email": False,
                "name": u"Tiny sprl",
                "street": u"Chaussee de Namur 40",
                "zip": u"1367",
            },
        )

    def test__som_report_comp_company__som(self):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        p_id = f.company_id.partner_id.id
        a_id = f.company_id.partner_id.address[0].id

        self.partner_obj.write(
            self.cursor,
            self.uid,
            p_id,
            {
                "name": "Som Energia, SCCL",
                "vat": "ESF55091367",
            },
        )
        self.par_add_obj.write(
            self.cursor,
            self.uid,
            a_id,
            {
                "phone": "872202550",
                "street": "generated",
                "nv": "Pic de Peguera",
                "pnp": "11",
                "es": "A",
                "pu": "8",
                "pt": "2",
                "tv": None,
                "city": "Girona",
                "zip": "17003",
                "email": "info@somenergia.coop",
            },
        )

        result = self.r_obj.get_component_company_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "cif": u"F55091367",
                "city": u"Girona",
                "email": u"info@somenergia.coop",
                "name": u"Som Energia, SCCL",
                "street": u"Pic de Peguera, 11 ESC. A 2 8",
                "zip": u"17003",
            },
        )


class Tests_FacturacioFacturaReport_gdo_component(Tests_FacturacioFacturaReport_base):
    def _test__som_report_comp_gdo__2019_es(self):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        p_id = f.partner_id.id

        self.setup_langs()

        self.partner_obj.write(self.cursor, self.uid, p_id, {"lang": "es_ES"})

        result = self.r_obj.get_component_gdo_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "wind_power": 359390,
                "photovoltaic": 75672,
                "hydraulics": 30034,
                "biogas": 7194,
                "total": 472290,
                "lang": u"es",
                "graph": "gdo_graf_es.png",
            },
        )

    def _test__som_report_comp_gdo__2019_cat(self):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        p_id = f.partner_id.id

        self.setup_langs()

        self.partner_obj.write(self.cursor, self.uid, p_id, {"lang": "ca_ES"})

        result = self.r_obj.get_component_gdo_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "wind_power": 359390,
                "photovoltaic": 75672,
                "hydraulics": 30034,
                "biogas": 7194,
                "total": 472290,
                "lang": u"ca",
                "graph": "gdo_graf_ca.png",
            },
        )


class Tests_FacturacioFacturaReport_flags_component(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    @mock.patch.object(giscedata_facturacio_report, "te_gkwh")
    def test__som_report_comp_flags_no_ghwk_no_auto(
        self, te_gkwh_mock_function, te_autoconsum_mock_function
    ):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        p_id = f.partner_id.id

        self.setup_langs()
        self.partner_obj.write(self.cursor, self.uid, p_id, {"lang": "es_ES"})
        te_gkwh_mock_function.return_value = False
        te_autoconsum_mock_function.return_value = False

        result = self.r_obj.get_component_flags_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "is_autoconsum": False,
                "autoconsum_flag": "flag_auto_little_es.png",
                "is_gkwh": False,
                "gkwh_flag": "flag_gkwh_little.png",
            },
        )

    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    @mock.patch.object(giscedata_facturacio_report, "te_gkwh")
    def test__som_report_comp_flags_no_ghwk_auto_ca(
        self, te_gkwh_mock_function, te_autoconsum_mock_function
    ):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        p_id = f.partner_id.id

        self.setup_langs()
        self.partner_obj.write(self.cursor, self.uid, p_id, {"lang": "ca_ES"})
        te_gkwh_mock_function.return_value = False
        te_autoconsum_mock_function.return_value = True

        result = self.r_obj.get_component_flags_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "is_autoconsum": True,
                "autoconsum_flag": "flag_auto_little_ca.png",
                "is_gkwh": False,
                "gkwh_flag": "flag_gkwh_little.png",
            },
        )

    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    @mock.patch.object(giscedata_facturacio_report, "te_gkwh")
    def test__som_report_comp_flags_no_ghwk_auto_es(
        self, te_gkwh_mock_function, te_autoconsum_mock_function
    ):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        p_id = f.partner_id.id

        self.setup_langs()
        self.partner_obj.write(self.cursor, self.uid, p_id, {"lang": "es_ES"})
        te_gkwh_mock_function.return_value = False
        te_autoconsum_mock_function.return_value = True

        result = self.r_obj.get_component_flags_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "is_autoconsum": True,
                "autoconsum_flag": "flag_auto_little_es.png",
                "is_gkwh": False,
                "gkwh_flag": "flag_gkwh_little.png",
            },
        )

    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    @mock.patch.object(giscedata_facturacio_report, "te_gkwh")
    def test__som_report_comp_flags_ghwk_no_auto(
        self, te_gkwh_mock_function, te_autoconsum_mock_function
    ):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        partner_id = f.partner_id.id

        self.setup_langs()
        self.partner_obj.write(self.cursor, self.uid, partner_id, {"lang": "es_ES"})
        te_gkwh_mock_function.return_value = True
        te_autoconsum_mock_function.return_value = False

        result = self.r_obj.get_component_flags_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "is_autoconsum": False,
                "autoconsum_flag": "flag_auto_little_es.png",
                "is_gkwh": True,
                "gkwh_flag": "flag_gkwh_little.png",
            },
        )

    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    @mock.patch.object(giscedata_facturacio_report, "te_gkwh")
    def test__som_report_comp_flags_ghwk_auto_ca(
        self, te_gkwh_mock_function, te_autoconsum_mock_function
    ):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        partner_id = f.partner_id.id

        self.setup_langs()
        self.partner_obj.write(self.cursor, self.uid, partner_id, {"lang": "ca_ES"})
        te_gkwh_mock_function.return_value = True
        te_autoconsum_mock_function.return_value = True

        result = self.r_obj.get_component_flags_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "is_autoconsum": True,
                "autoconsum_flag": "flag_auto_little_ca.png",
                "is_gkwh": True,
                "gkwh_flag": "flag_gkwh_little.png",
            },
        )

    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    @mock.patch.object(giscedata_facturacio_report, "te_gkwh")
    def test__som_report_comp_flags_ghwk_auto_es(
        self, te_gkwh_mock_function, te_autoconsum_mock_function
    ):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        partner_id = f.partner_id.id

        self.setup_langs()
        self.partner_obj.write(self.cursor, self.uid, partner_id, {"lang": "es_ES"})
        te_gkwh_mock_function.return_value = True
        te_autoconsum_mock_function.return_value = True

        result = self.r_obj.get_component_flags_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "is_autoconsum": True,
                "autoconsum_flag": "flag_auto_little_es.png",
                "is_gkwh": True,
                "gkwh_flag": "flag_gkwh_little.png",
            },
        )


class Tests_FacturacioFacturaReport_renovation_date(Tests_FacturacioFacturaReport_base):
    def test_get_renovation_date__leap_year_29_2_2016_2020(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2016-02-29", datetime(2020, 7, 14)
        )
        self.assertTrue(result == "2021-02-28")

    def test_get_renovation_date__leap_year_29_2_2020_2020(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2020-02-29", datetime(2020, 7, 14)
        )
        self.assertTrue(result == "2021-02-28")

    def test_get_renovation_date__leap_year_before_2020(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2016-09-08", datetime(2020, 7, 14)
        )
        self.assertTrue(result == "2020-09-08")

    def test_get_renovation_date__leap_year_after_2020(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2016-01-12", datetime(2020, 7, 14)
        )
        self.assertTrue(result == "2021-01-12")

    def test_get_renovation_date__leap_year_28_2_2020(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2020-02-28", datetime(2020, 7, 14)
        )
        self.assertTrue(result == "2021-02-28")

    def test_get_renovation_date__leap_year_29_2_and_leap_year_2020(self):
        result = giscedata_facturacio_report.get_renovation_date("2020-02-29", datetime(2020, 1, 1))
        self.assertTrue(result == "2020-02-29")

    def test_get_renovation_date__no_leap_year_before_2020(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2010-08-27", datetime(2020, 7, 14)
        )
        self.assertTrue(result == "2020-08-27")

    def test_get_renovation_date__no_leap_year_after_2020(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2010-01-27", datetime(2020, 7, 14)
        )
        self.assertTrue(result == "2021-01-27")

    def test_get_renovation_date__leap_year_29_2_2016_2022(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2016-02-29", datetime(2022, 3, 12)
        )
        self.assertTrue(result == "2023-02-28")

    def test_get_renovation_date__leap_year_29_2_2020_2022(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2020-02-29", datetime(2022, 3, 12)
        )
        self.assertTrue(result == "2023-02-28")

    def test_get_renovation_date__leap_year_before_2022(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2016-09-08", datetime(2022, 3, 12)
        )
        self.assertTrue(result == "2022-09-08")

    def test_get_renovation_date__leap_year_after_2022(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2016-01-12", datetime(2022, 3, 12)
        )
        self.assertTrue(result == "2023-01-12")

    def test_get_renovation_date__leap_year_28_2_2022(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2020-02-28", datetime(2022, 3, 12)
        )
        self.assertTrue(result == "2023-02-28")

    def test_get_renovation_date__leap_year_29_2_2022(self):
        result = giscedata_facturacio_report.get_renovation_date("2020-02-29", datetime(2022, 1, 1))
        self.assertTrue(result == "2022-02-28")

    def test_get_renovation_date__no_leap_year_before_2022(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2010-08-27", datetime(2022, 3, 12)
        )
        self.assertTrue(result == "2022-08-27")

    def test_get_renovation_date__no_leap_year_after_2022(self):
        result = giscedata_facturacio_report.get_renovation_date(
            "2010-01-27", datetime(2022, 3, 12)
        )
        self.assertTrue(result == "2023-01-27")


class Tests_FacturacioFacturaReport_contract_data_component(Tests_FacturacioFacturaReport_base):
    maxDiff = None

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_auvi_data"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "is_visible_readings_g_table"
    )
    @mock.patch.object(giscedata_facturacio_report, "get_renovation_date")
    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum_collectiu")
    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    def test_som_report_comp_contract_data_20A_no_auto(
        self,
        te_autoconsum_mock_function,
        te_autoconsum_collectiu_mock_function,
        get_renovation_date_mock_function,
        is_visible_readings_g_table_mock_function,
        get_auvi_data_mock_function,
    ):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        is_visible_readings_g_table_mock_function.return_value = True
        get_renovation_date_mock_function.return_value = "2021-01-01"
        te_autoconsum_mock_function.return_value = False
        te_autoconsum_collectiu_mock_function.return_value = False
        get_auvi_data_mock_function.return_value = False

        result = self.r_obj.get_component_contract_data_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "power": 6.0,
                "autoconsum": u"00",
                "powers": [("P1", 6.0)],
                "renovation_date": "2021-01-01",
                "cups": u"ES1234000000000001JN0F",
                "tariff": u"2.0A",
                "invoicing_mode": u"atr",
                "pricelist": u"TARIFAS ELECTRICIDAD",
                "autoconsum_cau": "",
                "is_autoconsum_colectiu": False,
                "cups_direction": u"carrer inventat ,  1  ESC.  1 1 1 aclaridor 00001 (Poble de Prova)",  # noqa: E501
                "autoconsum_colectiu_repartiment": 100.0,
                "cnae": u"0111",
                "power_invoicing_type": True,
                "remote_managed_meter": True,
                "is_autoconsum": False,
                "start_date": "2016-01-01",
                "small_text": False,
                "is_auvi": False,
                "auvi_data": False,
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_auvi_data"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "is_visible_readings_g_table"
    )
    @mock.patch.object(giscedata_facturacio_report, "get_renovation_date")
    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum_collectiu")
    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    def test_som_report_comp_contract_data_20A_amb_auto(
        self,
        te_autoconsum_mock_function,
        te_autoconsum_collectiu_mock_function,
        get_renovation_date_mock_function,
        is_visible_readings_g_table_mock_function,
        get_auvi_data_mock_function,
    ):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        p_id = self.get_fixture("giscedata_polissa", "polissa_autoconsum_01")
        self.factura_obj.write(self.cursor, self.uid, f_id, {"polissa_id": p_id})

        is_visible_readings_g_table_mock_function.return_value = True
        get_renovation_date_mock_function.return_value = "2021-01-01"
        te_autoconsum_mock_function.return_value = True
        te_autoconsum_collectiu_mock_function.return_value = False
        get_auvi_data_mock_function.return_value = False

        result = self.r_obj.get_component_contract_data_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        dict_expected = {
            "power": 4.6,
            "autoconsum": u"21",
            "powers": [],
            "renovation_date": "2021-01-01",
            "cups": u"ES1234000000000001JN0F",
            "tariff": u"2.0A",
            "invoicing_mode": u"atr",
            "pricelist": u"TARIFAS ELECTRICIDAD",
            "autoconsum_cau": u"ES0318363477145938GEA000",
            "is_autoconsum_colectiu": False,
            "cups_direction": u"carrer inventat ,  1  ESC.  1 1 1 aclaridor 00001 (Poble de Prova)",  # noqa: E501
            "autoconsum_colectiu_repartiment": 100.0,
            "cnae": u"0111",
            "power_invoicing_type": False,
            "remote_managed_meter": True,
            "is_autoconsum": True,
            "start_date": "2012-01-01",
            "small_text": False,
            "is_auvi": False,
            "auvi_data": False,
        }
        self.assertDictEqual(
            result,
            dict_expected,
        )


class Tests_FacturacioFacturaReport_readings_table(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    def test__som_report_comp_readings_tables__days_equal_zero(
        self, te_autoconsum_mock_function, get_readings_data_mock_function
    ):
        get_readings_data_mock_function.return_value = (
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )
        te_autoconsum_mock_function.return_value = True

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.factura_obj.write(
            self.cursor,
            self.uid,
            f_id,
            {
                "data_inici": "2020-09-10",
                "data_final": "2020-09-09",
            },
        )
        result = self.r_obj.get_component_readings_table_data(**self.bfp(f_id))
        fact = self.bf(f_id)
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "periodes_a": 1,
                "lectures_a": 5,
                "total_lectures_a": 13,
                "dies_factura": 0,
                "diari_factura_actual_eur": fact.total_energia * 1.0,
                "diari_factura_actual_kwh": fact.energia_kwh * 1.0,
                "has_autoconsum": True,
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    def test__som_report_comp_readings_tables__days_equal_ten(
        self, te_autoconsum_mock_function, get_readings_data_mock_function
    ):
        get_readings_data_mock_function.return_value = (
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )
        te_autoconsum_mock_function.return_value = False

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.factura_obj.write(
            self.cursor,
            self.uid,
            f_id,
            {
                "data_inici": "2020-09-01",
                "data_final": "2020-09-10",
            },
        )

        result = self.r_obj.get_component_readings_table_data(**self.bfp(f_id))
        fact = self.bf(f_id)
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "periodes_a": 1,
                "lectures_a": 5,
                "total_lectures_a": 13,
                "dies_factura": 10,
                "diari_factura_actual_eur": fact.total_energia / 10.0,
                "diari_factura_actual_kwh": fact.energia_kwh / 10.0,
                "has_autoconsum": False,
            },
        )


class Tests_FacturacioFacturaReport_energy_consumption_graphic(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_historic_data"
    )
    def test__som_report_comp_ecg__days_equal_one(
        self, get_historic_data_mock_function, get_readings_data_mock_function
    ):
        get_historic_data_mock_function.return_value = (
            [
                {
                    "consum": 10,
                    "facturat": 10,
                    "data_ini": "2020-09-10",
                    "data_fin": "2020-09-10",
                    "mes": "2020/09",
                }
            ],
            2,
        )
        get_readings_data_mock_function.return_value = (
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.factura_obj.write(
            self.cursor,
            self.uid,
            f_id,
            {
                "data_inici": "2020-09-10",
            },
        )
        self.factura_obj.browse(self.cursor, self.uid, f_id)

        result = self.r_obj.get_component_energy_consumption_graphic_data(**self.bfp(f_id))
        fp = self.bfp(f_id)
        fact = fp["fact"]
        fp["pol"]

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "fact_id": fact.id,
                "total_historic_eur_dia": 10.0,
                "total_historic_kw_dia": 10.0,
                "historic_dies": 1.0,
                "total_any": 10,
                "historic_json": "2",
                "periodes_a": 1,
                "is_6X": False,
                "average_30_days": 0.0,
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_historic_data"
    )
    def test__som_report_comp_ecg__days_equal_ten(
        self, get_historic_data_mock_function, get_readings_data_mock_function
    ):
        get_historic_data_mock_function.return_value = (
            [
                {
                    "consum": 10,
                    "facturat": 10,
                    "data_ini": "2020-10-01",
                    "data_fin": "2020-10-11",
                    "mes": "2020/10",
                }
            ],
            2,
        )
        get_readings_data_mock_function.return_value = (
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.factura_obj.write(
            self.cursor,
            self.uid,
            f_id,
            {
                "data_inici": "2019-09-01",
            },
        )
        self.factura_obj.browse(self.cursor, self.uid, f_id)

        result = self.r_obj.get_component_energy_consumption_graphic_data(**self.bfp(f_id))
        fp = self.bfp(f_id)
        fact = fp["fact"]
        fp["pol"]

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "fact_id": fact.id,
                "total_historic_eur_dia": 1.0,
                "total_historic_kw_dia": 1.0,
                "historic_dies": 10,
                "total_any": 10,
                "historic_json": "2",
                "periodes_a": 1,
                "is_6X": False,
                "average_30_days": 10.0 / 30,
            },
        )


class Tests_FacturacioFacturaReport_meters(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    def test__som_report_comp_meters__without_readings(self, get_readings_data_mock_function):
        get_readings_data_mock_function.return_value = (
            1,
            2,
            3,
            4,
            [],
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_meters_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "location": "down",
                "show_component": False,
                "periodes_a": 1,
                "lectures_a": [],
                "total_lectures_a": 13,
                "lectures_real_a": 9,
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    def test__som_report_comp_meters__without_real_readings_down(
        self, get_readings_data_mock_function
    ):

        lectures_a = {0: {0: [0, 1, 2, 3, 4, 5, 6, "casa"]}}
        lectures_real_a = {0: [1, 2]}
        get_readings_data_mock_function.return_value = (
            [1, 2, 3],
            2,
            3,
            4,
            lectures_a,
            6,
            7,
            8,
            lectures_real_a,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_meters_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "location": "down",
                "show_component": True,
                "periodes_a": [1, 2, 3],
                "lectures_a": lectures_a,
                "total_lectures_a": 13,
                "lectures_real_a": lectures_real_a,
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    def test__som_report_comp_meters__without_real_readings_up(
        self, get_readings_data_mock_function
    ):

        lectures_a = {0: {0: [0, 1, 2, 3, 4, 5, 6, "casa"]}}
        lectures_real_a = {0: [1, 2]}
        get_readings_data_mock_function.return_value = (
            [1, 2],
            2,
            3,
            4,
            lectures_a,
            6,
            7,
            8,
            lectures_real_a,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_meters_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "location": "up",
                "show_component": True,
                "periodes_a": [1, 2],
                "lectures_a": lectures_a,
                "total_lectures_a": 13,
                "lectures_real_a": lectures_real_a,
            },
        )


class Tests_FacturacioFacturaReport_emergency_complaints(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_distri_phone"
    )
    def test__som_report_comp_emergency_complaints__no_agreement_partner(
        self, get_distri_phone_mock_funtion, get_readings_data_mock_function
    ):
        get_readings_data_mock_function.return_value = (
            [1, 2],
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )
        get_distri_phone_mock_funtion.return_value = "123456789"

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)

        p_id = 23
        self.partner_obj.write(self.cursor, self.uid, p_id, {"ref": "S12345"})
        self.polissa_obj.write(
            self.cursor,
            self.uid,
            f.polissa_id.id,
            {
                "ref_dist": "ref_dist",
            },
        )

        result = self.r_obj.get_component_emergency_complaints_data(**self.bfp(f_id))

        self.assertYamlfy(result)

        self.assertEquals(
            result,
            {
                "location": "up",
                "is_6X": False,
                "distri_name": "Agrolait",
                "distri_contract": u"ref_dist",
                "distri_phone": "123.456.789",
                "has_agreement_partner": False,
                "agreement_partner_name": False,
                "is_energetica": False,
                "comer_phone": u"(+32).81.81.37.00",
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_distri_phone"
    )
    def test__som_report_comp_emergency_complaints__agreement_partner(
        self, get_distri_phone_mock_funtion, get_readings_data_mock_function
    ):
        get_readings_data_mock_function.return_value = (
            [1, 2],
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )
        get_distri_phone_mock_funtion.return_value = "123456789"

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)

        p_id = 23
        self.partner_obj.write(self.cursor, self.uid, p_id, {"ref": "S019753"})
        self.polissa_obj.write(
            self.cursor, self.uid, f.polissa_id.id, {"ref_dist": "ref_dist", "soci": p_id}
        )

        result = self.r_obj.get_component_emergency_complaints_data(**self.bfp(f_id))

        self.assertYamlfy(result)

        self.assertEquals(
            result,
            {
                "location": "up",
                "is_6X": False,
                "distri_name": u"Agrolait",
                "distri_contract": u"ref_dist",
                "distri_phone": "123.456.789",
                "has_agreement_partner": True,
                "agreement_partner_name": u"ENDESA DISTRIBUCI\xd3N EL\xc9CTRICA S. L.",
                "is_energetica": True,
                "comer_phone": u"(+32).81.81.37.00",
            },
        )


class Tests_FacturacioFacturaReport_invoice_details_power(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_tarifa_elect_atr"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport,
        "get_total_excess_power_consumed",
    )
    def test__som_report_comp_invoice_details_power__without_linies_potencia(
        self, get_total_excess_power_consumed_mock_function, get_tarifa_elect_atr_mock_function
    ):

        get_total_excess_power_consumed_mock_function.return_value = [0.0, False]
        get_tarifa_elect_atr_mock_function.return_value = "res_id"

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        linies_potencia = []

        self.factura_obj.write(
            self.cursor,
            self.uid,
            f_id,
            {
                "data_inici": "2019-09-01",
                "linies_potencia": linies_potencia,
            },
        )
        self.factura_obj.browse(self.cursor, self.uid, f_id)

        result = self.r_obj.get_component_invoice_details_power_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "power_lines": [],
                "atr_power_lines": {},
                "is_6X": False,
                "total_exces_consumida": 0.0,
                "is_power_tolls_visible": False,
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_tarifa_elect_atr"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_atr_price"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport,
        "get_total_excess_power_consumed",
    )
    def test__som_report_comp_invoice_details_power__with_linies_potencia(
        self,
        get_total_excess_power_consumed_mock_function,
        get_atr_price_mock_function,
        get_tarifa_elect_atr_mock_function,
    ):

        get_total_excess_power_consumed_mock_function.return_value = [10.0, False]
        get_atr_price_mock_function.return_value = 10.0
        get_tarifa_elect_atr_mock_function.return_value = "res_id"

        f_id = self.get_fixture("giscedata_facturacio", "factura_0004")

        l_ids = self.linia_f_obj.search(
            self.cursor, self.uid, [("factura_id", "=", f_id), ("tipus", "=", "potencia")]
        )

        self.linia_f_obj.write(
            self.cursor,
            self.uid,
            l_ids,
            {
                "data_desde": "2017-09-01",
            },
        )

        self.factura_obj.browse(self.cursor, self.uid, f_id)

        result = self.r_obj.get_component_invoice_details_power_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "power_lines": [
                    {
                        "multi": 1.0,
                        "name": u"linia_0004",
                        "days_per_year": 365,
                        "price_subtotal": 11.49,
                        "atr_price": 10.0,
                        "quantity": 100.0,
                    }
                ],
                "is_power_tolls_visible": False,
                "total_exces_consumida": 10.0,
                "is_6X": False,
                "atr_power_lines": {
                    u"li": {
                        "atrprice_subtotal": 0.0,
                        "price": 10.0,
                        "multi": 1.0,
                        "days_per_year": 365,
                        "quantity": 100.0,
                    }
                },
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_tarifa_elect_atr"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_atr_price"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport,
        "get_total_excess_power_consumed",
    )
    def test__som_report_comp_invoice_details_power__with_linies_potencia_leap_year(
        self,
        get_total_excess_power_consumed_mock_function,
        get_atr_price_mock_function,
        get_tarifa_elect_atr_mock_function,
    ):

        get_total_excess_power_consumed_mock_function.return_value = [10.0, False]
        get_atr_price_mock_function.return_value = 10.0
        get_tarifa_elect_atr_mock_function.return_value = "res_id"

        f_id = self.get_fixture("giscedata_facturacio", "factura_0004")

        l_ids = self.linia_f_obj.search(
            self.cursor, self.uid, [("factura_id", "=", f_id), ("tipus", "=", "potencia")]
        )

        self.linia_f_obj.write(
            self.cursor,
            self.uid,
            l_ids,
            {
                "data_desde": "2012-09-01",
            },
        )

        self.factura_obj.browse(self.cursor, self.uid, f_id)

        result = self.r_obj.get_component_invoice_details_power_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "power_lines": [
                    {
                        "multi": 1.0,
                        "name": u"linia_0004",
                        "days_per_year": 366,
                        "price_subtotal": 11.49,
                        "atr_price": 10.0,
                        "quantity": 100.0,
                    }
                ],
                "is_power_tolls_visible": False,
                "total_exces_consumida": 10.0,
                "is_6X": False,
                "atr_power_lines": {
                    u"li": {
                        "atrprice_subtotal": 0.0,
                        "price": 10.0,
                        "multi": 1.0,
                        "days_per_year": 366,
                        "quantity": 100.0,
                    }
                },
            },
        )


class Tests_FacturacioFacturaReport_invoice_details_energy(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_real_energy_lines"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_tarifa_elect_atr"
    )
    def test__som_report_comp_invoice_details_energy__without_energy_lines(
        self, get_tarifa_elect_atr_mock_function, get_real_energy_lines_mock_function
    ):

        get_tarifa_elect_atr_mock_function.return_value = "res_id"
        get_real_energy_lines_mock_function.return_value = []

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        l_ids = self.linia_f_obj.search(self.cursor, self.uid, [("tipus", "=", "energia")])
        self.linia_f_obj.write(self.cursor, self.uid, l_ids, {"tipus": "potencia"})

        result = self.r_obj.get_component_invoice_details_energy_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {"energy_lines": [], "atr_energy_lines": {}, "is_new_tariff_message_visible": False},
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_lines_in_extralines"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_gkwh_owner"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_atr_price"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_tarifa_elect_atr"
    )
    def test__som_report_comp_invoice_details_energy__with_energy_lines(
        self,
        get_tarifa_elect_atr_mock_function,
        get_atr_price_mock_function,
        get_gkwh_owner_mock_function,
        get_lines_in_extralines_mock_function,
    ):

        get_tarifa_elect_atr_mock_function.return_value = "res_id"
        get_atr_price_mock_function.return_value = 10.0
        get_gkwh_owner_mock_function.return_value = "noms_i_cognoms"
        get_lines_in_extralines_mock_function.return_value = []

        f_id = self.get_fixture("giscedata_facturacio", "factura_0008")

        l_ids = self.linia_f_obj.search(
            self.cursor, self.uid, [("factura_id", "=", f_id), ("tipus", "=", "energia")]
        )

        self.linia_f_obj.write(
            self.cursor,
            self.uid,
            l_ids,
            {
                "data_desde": "2012-09-01",
            },
        )

        result = self.r_obj.get_component_invoice_details_energy_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "energy_lines": [
                    {
                        "name": u"P1",
                        "quantity": 5000.0,
                        "price_unit_multi": 0.108728,
                        "price_subtotal": 543.64,
                        "gkwh_owner": "noms_i_cognoms",
                    }
                ],
                "atr_energy_lines": {
                    u"P1": {"atrprice_subtotal": 0.0, "price": 10.0, "quantity": 5000.0}
                },
                "is_new_tariff_message_visible": False,
            },
        )


class Tests_FacturacioFacturaReport_invoice_details_generation(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport,
        "get_autoconsum_excedents_product_id",
    )
    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    def test__som_report_comp_invoice_details_generation__without_generation_lines(
        self, te_autoconsum_mock_function, get_autoconsum_excedents_product_id_mock_function
    ):
        te_autoconsum_mock_function.return_value = False
        get_autoconsum_excedents_product_id_mock_function.return_value = 1

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_invoice_details_generation_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "generation_lines": [],
                "has_autoconsum": False,
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport,
        "get_autoconsum_excedents_product_id",
    )
    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    def test__som_report_comp_invoice_details_generation__with_generation_lines_without_auto(
        self, te_autoconsum_mock_function, get_autoconsum_excedents_product_id_mock_function
    ):
        te_autoconsum_mock_function.return_value = False
        get_autoconsum_excedents_product_id_mock_function.return_value = 1

        f_id = self.get_fixture("giscedata_facturacio", "factura_0008")
        l_ids = self.linia_f_obj.search(
            self.cursor, self.uid, [("factura_id", "=", f_id), ("tipus", "=", "lloguer")]
        )

        self.linia_f_obj.write(
            self.cursor,
            self.uid,
            l_ids,
            {
                "data_desde": "2012-09-01",
                "tipus": "generacio",
            },
        )

        result = self.r_obj.get_component_invoice_details_generation_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "generation_lines": [
                    {
                        "is_visible": True,
                        "name": u"P1",
                        "price_subtotal": 3.0,
                        "price_unit_multi": 0.05,
                        "quantity": 60.0,
                    }
                ],
                "has_autoconsum": False,
            },
        )


class Tests_FacturacioFacturaReport_invoice_details_reactive(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_tarifa_elect_atr"
    )
    def test__som_report_comp_invoice_details_reactive__without_reactive_lines(
        self, get_tarifa_elect_atr_mock_function
    ):
        get_tarifa_elect_atr_mock_function.return_value = "res_id"

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_invoice_details_reactive_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "reactive_lines": [],
                "is_visible": False,
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_atr_price"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_tarifa_elect_atr"
    )
    def test__som_report_comp_invoice_details_reactive__with_reactive_lines(
        self, get_tarifa_elect_atr_mock_function, get_atr_price_mock_function
    ):
        get_tarifa_elect_atr_mock_function.return_value = "res_id"
        get_atr_price_mock_function.return_value = 10.0

        f_id = self.get_fixture("giscedata_facturacio", "factura_0008")

        l_ids = self.linia_f_obj.search(
            self.cursor, self.uid, [("factura_id", "=", f_id), ("tipus", "=", "lloguer")]
        )

        self.linia_f_obj.write(
            self.cursor,
            self.uid,
            l_ids,
            {
                "data_desde": "2012-09-01",
                "tipus": "reactiva",
            },
        )

        result = self.r_obj.get_component_invoice_details_reactive_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "reactive_lines": [
                    {
                        "atr_price": 10.0,
                        "atrprice_subtotal": 0.0,
                        "name": u"P1",
                        "price_subtotal": 3.0,
                        "price_unit_multi": 0.05,
                        "quantity": 60.0,
                    }
                ],
                "is_visible": True,
            },
        )


class Tests_FacturacioFacturaReport_invoice_details_other_concepts(
    Tests_FacturacioFacturaReport_base
):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_lines_in_extralines"
    )
    def test__som_report_comp_invoice_details_other_concepts__without_other_lines(
        self, get_lines_in_extralines_mock_function
    ):

        get_lines_in_extralines_mock_function.return_value = []
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        fiscal_pos_obj = self.model("account.fiscal.position")
        fiscal_pos_ids = fiscal_pos_obj.search(self.cursor, self.uid, [], limit=1)

        self.factura_obj.write(
            self.cursor,
            self.uid,
            f_id,
            {
                "fiscal_position": fiscal_pos_ids[0],
            },
        )

        result = self.r_obj.get_component_invoice_details_other_concepts_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "lloguer_lines": [],
                "bosocial_lines": [],
                "donatiu_lines": [],
                "compl_lines": [],
                "altres_lines": [],
                "iese_lines": [],
                "iva_lines": [],
                "igic_lines": [],
                "fiscal_position": False,
                "excempcio": None,
                "percentatges_exempcio_splitted": None,
                "percentatges_exempcio": None,
                "is_excempcio_IE_base": None,
                "donatiu": 0,
                "amount_total": 10.0,
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_lines_in_extralines"
    )
    def test__som_report_comp_invoice_details_other_concepts__with_lloguer(
        self, get_lines_in_extralines_mock_function
    ):

        get_lines_in_extralines_mock_function.return_value = []
        f_id = self.get_fixture("giscedata_facturacio", "factura_0008")
        fiscal_pos_obj = self.model("account.fiscal.position")
        fiscal_pos_ids = fiscal_pos_obj.search(self.cursor, self.uid, [], limit=1)

        l_ids = self.linia_f_obj.search(
            self.cursor, self.uid, [("factura_id", "=", f_id), ("tipus", "=", "lloguer")]
        )

        self.linia_f_obj.write(
            self.cursor,
            self.uid,
            l_ids,
            {
                "data_desde": "2012-09-01",
            },
        )

        self.factura_obj.write(
            self.cursor,
            self.uid,
            f_id,
            {
                "fiscal_position": fiscal_pos_ids[0],
            },
        )

        result = self.r_obj.get_component_invoice_details_other_concepts_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "lloguer_lines": [
                    {
                        "quantity": 60.0,
                        "price_unit": 0.05,
                        "price_subtotal": 3.0,
                        "iva": "",
                    }
                ],
                "bosocial_lines": [],
                "compl_lines": [],
                "donatiu_lines": [],
                "altres_lines": [],
                "iese_lines": [],
                "iva_lines": [],
                "igic_lines": [],
                "fiscal_position": False,
                "excempcio": None,
                "percentatges_exempcio_splitted": None,
                "percentatges_exempcio": None,
                "is_excempcio_IE_base": None,
                "donatiu": 0,
                "amount_total": 547.36,
            },
        )


class Tests_FacturacioFacturaReport_invoice_details_comments(Tests_FacturacioFacturaReport_base):
    def test__som_report_comp_invoice_details_comments__without_comments(self):

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_invoice_details_comments_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "invoice_comment": None,
                "has_web": False,
                "web_distri": False,
                "language": False,
                "distri_name": u"Agrolait",
            },
        )

    def test__som_report_comp_invoice_details_comments__with_comments(self):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        f = self.factura_obj.browse(self.cursor, self.uid, f_id)

        journal_id = f.journal_id.id
        journal_obj = self.model("account.journal")
        journal_obj.write(
            self.cursor,
            self.uid,
            journal_id,
            {
                "code": "RECUPERACION_IVA",
            },
        )

        self.factura_obj.write(
            self.cursor,
            self.uid,
            f_id,
            {
                "comment": "comment",
            },
        )

        result = self.r_obj.get_component_invoice_details_comments_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "invoice_comment": u"comment",
                "has_web": False,
                "web_distri": False,
                "language": False,
                "distri_name": u"Agrolait",
            },
        )


class Tests_FacturacioFacturaReport_amount_destination(Tests_FacturacioFacturaReport_base):
    def test__som_report_comp_amount_destination__without_altres_lines(self):

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_amount_destination_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "is_visible": True,
                "factura_id": 1,
                "amount_total": 10.0,
                "total_lloguers": 0.0,
                "pie_total": 10.0,
                "pie_regulats": 0.0,
                "pie_impostos": 0.0,
                "pie_costos": 10.0,
                "rep_BOE": {"i": 39.44, "c": 40.33, "o": 20.23},
            },
        )

    def test__som_report_comp_amount_destination__with_altres_lines(self):

        f_id = self.get_fixture("giscedata_facturacio", "factura_0008")
        product_obj = self.model("product.product")
        product_id = product_obj.search(self.cursor, self.uid, [], limit=1)[0]

        product_obj.write(
            self.cursor,
            self.uid,
            product_id,
            {
                "default_code": "AAA",
            },
        )

        l_ids = self.linia_f_obj.search(
            self.cursor, self.uid, [("factura_id", "=", f_id), ("tipus", "=", "lloguer")]
        )

        self.linia_f_obj.write(
            self.cursor,
            self.uid,
            l_ids,
            {"data_desde": "2012-09-01", "tipus": "altres", "product_id": product_id},
        )

        result = self.r_obj.get_component_amount_destination_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "is_visible": True,
                "factura_id": 14,
                "amount_total": 547.36,
                "total_lloguers": 0.0,
                "pie_total": 547.36,
                "pie_regulats": 3.0,
                "pie_impostos": 0.0,
                "pie_costos": 544.36,
                "rep_BOE": {"i": 39.44, "c": 40.33, "o": 20.23},
            },
        )


class Tests_FacturacioFacturaReport_reactive_readings_table(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport,
        "is_visible_reactive_and_maximeter",
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "is_visible_reactive"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    def test__som_report_comp_reactive_readings_table__with_readings(
        self,
        get_readings_data_mock_function,
        is_visible_reactive_mock_function,
        is_visible_reactive_and_maximeter_mock_function,
    ):
        get_readings_data_mock_function.return_value = (
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )
        is_visible_reactive_mock_function.return_value = True
        is_visible_reactive_and_maximeter_mock_function.return_value = False

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_reactive_readings_table_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "visible_side_by_side": "",
                "is_visible": True,
                "periodes_r": 2,
                "lectures_r": 6,
                "lectures_real_r": 10,
                "total_lectures_r": 14,
            },
        )


class Tests_FacturacioFacturaReport_maximeter_readings_table(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport,
        "is_visible_reactive_and_maximeter",
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "is_visible_reactive"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    def test__som_report_comp_maximeter_readings_table__with_readings_without_exces_potencia(
        self,
        get_readings_data_mock_function,
        is_visible_reactive_mock_function,
        is_visible_reactive_and_maximeter_mock_function,
    ):
        get_readings_data_mock_function.return_value = (
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )
        is_visible_reactive_mock_function.return_value = True
        is_visible_reactive_and_maximeter_mock_function.return_value = False

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_maximeter_readings_table_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "visible_side_by_side": "",
                "is_visible": True,
                "periodes_r": 2,
                "has_exces_potencia": 0,
                "exces_m": [],
                "periodes_m": [],
                "lectures_m": [],
                "fact_potencia": {},
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport,
        "is_visible_reactive_and_maximeter",
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "is_visible_reactive"
    )
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_readings_data"
    )
    def test__som_report_comp_maximeter_readings_table__with_readings_with_exces_potencia(
        self,
        get_readings_data_mock_function,
        is_visible_reactive_mock_function,
        is_visible_reactive_and_maximeter_mock_function,
    ):
        get_readings_data_mock_function.return_value = (
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
        )
        is_visible_reactive_mock_function.return_value = True
        is_visible_reactive_and_maximeter_mock_function.return_value = False

        f_id = self.get_fixture("giscedata_facturacio", "factura_0008")

        l_ids = self.linia_f_obj.search(
            self.cursor, self.uid, [("factura_id", "=", f_id), ("tipus", "=", "lloguer")]
        )

        self.linia_f_obj.write(
            self.cursor,
            self.uid,
            l_ids,
            {
                "data_desde": "2012-09-01",
                "tipus": "exces_potencia",
            },
        )

        result = self.r_obj.get_component_maximeter_readings_table_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "visible_side_by_side": "",
                "is_visible": True,
                "periodes_r": 2,
                "has_exces_potencia": 1,
                "exces_m": [(60.0, 3.0)],
                "periodes_m": [u"P1"],
                "lectures_m": [(u"P1", 6.0, 0.0)],
                "fact_potencia": {u"P1": 6.928},
            },
        )


class Tests_FacturacioFacturaReport_invoice_info(Tests_FacturacioFacturaReport_base):
    def test__som_report_comp_invoice_info__without_agreement(self):

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.factura_obj.browse(self.cursor, self.uid, f_id)

        self.factura_obj.write(
            self.cursor, self.uid, f_id, {"date_due": "01/01/2016", "number": "0001/F"}
        )

        result = self.r_obj.get_component_invoice_info_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "has_agreement_partner": False,
                "amount_total": 10.0,
                "type": u"out_invoice",
                "number": u"0001/F",
                "ref": False,
                "ref_number": False,
                "date_invoice": "01/03/2016",
                "start_date": "01/01/2016",
                "end_date": "29/02/2016",
                "contract_number": u"0001C",
                "address": u"carrer inventat ,  1  ESC.  1 1 1 aclaridor 00001 (Poble de Prova)",
                "due_date": "01/01/2016",
            },
        )


class Tests_FacturacioFacturaReport_invoice_summary(Tests_FacturacioFacturaReport_base):
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_extra_energy_lines"
    )
    @mock.patch.object(giscedata_facturacio_report, "te_autoconsum")
    def test__som_report_comp_invoice_summary__only_energy(
        self, te_autoconsum_mock_function, get_extra_energy_lines_mock_function
    ):
        te_autoconsum_mock_function.return_value = False
        get_extra_energy_lines_mock_function.return_value = []

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_component_invoice_summary_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "total_exces_consumida": 0.0,
                "has_exces_potencia": False,
                "total_energy": 10.0,
                "total_power": 0.0,
                "total_ractive": 0.0,
                "total_rent": 0.0,
                "total_amount": 10.0,
                "has_autoconsum": False,
                "autoconsum_total_compensada": 0,
                "impostos": {},
                "iese": 0,
                "donatiu": 0,
                "total_bosocial": 0,
                "total_altres": 0,
            },
        )


class Tests_FacturacioFacturaReport_partner_info(Tests_FacturacioFacturaReport_base):
    def test__som_report_comp_partner_info(self):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        partner_bank_id = self.partner_bank_obj.search(self.cursor, self.uid, [], limit=1)[0]
        self.partner_bank_obj.write(
            self.cursor,
            self.uid,
            partner_bank_id,
            {
                "name": "evil bank",
                "iban": "ES12 3456 7890 1234 1234 1234",
            },
        )

        f = self.factura_obj.browse(self.cursor, self.uid, f_id)
        self.payment_type_obj.write(
            self.cursor, self.uid, f.polissa_id.tipo_pago.id, {"code": "TRANSFERENCIA_SBC"}
        )
        self.factura_obj.write(self.cursor, self.uid, f_id, {"partner_bank": partner_bank_id})

        result = self.r_obj.get_component_partner_info_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "pol_name": u"Camptocamp",
                "vat": u"B82420654",
                "is_out_refund": False,
                "payment_type": u"TRANSFERENCIA_SBC",
                "cc_name": u"**** **** **** **** **** 1234",
                "bank_name": u"",
            },
        )


class Tests_FacturacioFacturaReport_invoice_details_td(Tests_FacturacioFacturaReport_base):

    # TODO
    # get_matrix_show_periods
    # get_component_invoice_details_td_data
    # get_sub_component_invoice_details_td_power_data
    # get_sub_component_invoice_details_td_power_tolls_data
    # get_sub_component_invoice_details_td_power_charges_data
    # get_component_invoice_details_info_td_data

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_tarifa_elect_atr"
    )
    def test__get_sub_component_invoice_details_td_power_tolls_data_dummy(
        self, get_tarifa_elect_atr_mock_function
    ):
        get_tarifa_elect_atr_mock_function.return_value = "res_id"

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_sub_component_invoice_details_td_power_tolls_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "showing_periods": ["P1", "P2", "P3", "P4", "P5", "P6"],
                "dies_any": 0,
                "dies": 0,
                "iva_column": False,
            },
        )

    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_tarifa_elect_atr"
    )
    def test__get_sub_component_invoice_details_td_power_charges_data_dummy(
        self, get_tarifa_elect_atr_mock_function
    ):
        get_tarifa_elect_atr_mock_function.return_value = "res_id"

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        result = self.r_obj.get_sub_component_invoice_details_td_power_charges_data(
            discount={"is_visible": False}, **self.bfp(f_id)
        )

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "showing_periods": ["P1", "P2", "P3", "P4", "P5", "P6"],
                "dies_any": 0,
                "dies": 0,
                "header_multi": 2,
                "iva_column": False,
            },
        )

    @mock.patch.object(giscedata_facturacio_report, "is_2XTD")
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_atr_price"
    )
    def test__get_sub_component_invoice_details_td_2_power_lines_2_periods_1_block(
        self, get_atr_price_mock_function, is_2XTD_mock_function
    ):
        get_atr_price_mock_function.return_value = 10.0
        is_2XTD_mock_function.return_value = True

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P1",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P2",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        fact_pol = self.bfp(f_id)
        result = self.r_obj.get_sub_component_invoice_details_td(
            fact_pol["fact"], fact_pol["pol"], fact_pol["fact"].linies_potencia
        )
        self.assertEquals(
            result,
            [
                {
                    "P1": {
                        "quantity": 1,
                        "atr_price": 10.0,
                        "price_subtotal": 1.0,
                        "price_unit_multi": 1.0,
                        "price_unit": 1.0,
                        "extra": 1.0,
                    },
                    "P2": {
                        "quantity": 1,
                        "atr_price": 10.0,
                        "price_subtotal": 1.0,
                        "price_unit_multi": 1.0,
                        "price_unit": 1.0,
                        "extra": 1.0,
                    },
                    "multi": 1.0,
                    "days_per_year": 365,
                    "total": 2.0,
                    "origin": "sense lectura",
                    "data": "2021-06-01",
                    "days": 30,
                    "date_from": "01/06/2021",
                    "date_to": "30/06/2021",
                    "date_to_d": "2021-06-30",
                    "iva": "",
                }
            ],
        )

    @mock.patch.object(giscedata_facturacio_report, "is_2XTD")
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_atr_price"
    )
    def test__get_sub_component_invoice_details_td_data_4_power_lines_2_periods_2_blocks(
        self, get_atr_price_mock_function, is_2XTD_mock_function
    ):
        get_atr_price_mock_function.return_value = 10.0
        is_2XTD_mock_function.return_value = True

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P1",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-05-31",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P2",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-05-31",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P1",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 1,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P2",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 1,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        result = self.r_obj.get_sub_component_invoice_details_td_power_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "header_multi": 6,
                "showing_periods": ["P1", "P2", "P3"],
                "iva_column": False,
                "power_lines_data": [
                    {
                        "P1": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P2": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "multi": 1.0,
                        "days_per_year": 365,
                        "total": 2.0,
                        "origin": "sense lectura",
                        "data": "2021-05-01",
                        "days": 31,
                        "date_from": "01/05/2021",
                        "date_to": "31/05/2021",
                        "date_to_d": "2021-05-31",
                        "iva": "",
                    },
                    {
                        "P1": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P2": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "multi": 1.0,
                        "days_per_year": 365,
                        "total": 2.0,
                        "origin": "sense lectura",
                        "data": "2021-06-01",
                        "days": 30,
                        "date_from": "01/06/2021",
                        "date_to": "30/06/2021",
                        "date_to_d": "2021-06-30",
                        "iva": "",
                    },
                ],
            },
        )

    @mock.patch.object(giscedata_facturacio_report, "is_2XTD")
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_atr_price"
    )
    def test__get_sub_component_invoice_details_td_data_4_power_lines_2_periods_2_blocks_incomplete(
        self, get_atr_price_mock_function, is_2XTD_mock_function
    ):
        get_atr_price_mock_function.return_value = 10.0
        is_2XTD_mock_function.return_value = True

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P1",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-05-31",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P2",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P1",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 1,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        result = self.r_obj.get_sub_component_invoice_details_td_power_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "header_multi": 6,
                "showing_periods": ["P1", "P2", "P3"],
                "iva_column": False,
                "power_lines_data": [
                    {
                        "P1": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P2": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "multi": 1.0,
                        "days_per_year": 365,
                        "total": 2.0,
                        "origin": "sense lectura",
                        "data": "2021-05-01",
                        "days": 61,
                        "date_from": "01/05/2021",
                        "date_to": "31/05/2021",
                        "date_to_d": "2021-05-31",
                        "iva": "",
                    },
                    {
                        "P1": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "multi": 1.0,
                        "days_per_year": 365,
                        "total": 1.0,
                        "origin": "sense lectura",
                        "data": "2021-06-01",
                        "days": 30,
                        "date_from": "01/06/2021",
                        "date_to": "30/06/2021",
                        "date_to_d": "2021-06-30",
                        "iva": "",
                    },
                ],
            },
        )

    @mock.patch.object(giscedata_facturacio_report, "is_2XTD")
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_atr_price"
    )
    def test__get_sub_component_invoice_details_td_data_4_power_lines_3_periods_2_blocks_incomplete(
        self, get_atr_price_mock_function, is_2XTD_mock_function
    ):
        get_atr_price_mock_function.return_value = 10.0
        is_2XTD_mock_function.return_value = True

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P1",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-05-31",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P2",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P3",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P1",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 1,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        result = self.r_obj.get_sub_component_invoice_details_td_power_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "header_multi": 6,
                "showing_periods": ["P1", "P2", "P3"],
                "iva_column": False,
                "power_lines_data": [
                    {
                        "P1": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P2": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P3": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "multi": 1.0,
                        "days_per_year": 365,
                        "total": 3.0,
                        "origin": "sense lectura",
                        "data": "2021-05-01",
                        "days": 61,
                        "date_from": "01/05/2021",
                        "date_to": "31/05/2021",
                        "date_to_d": "2021-05-31",
                        "iva": "",
                    },
                    {
                        "P1": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "multi": 1.0,
                        "days_per_year": 365,
                        "total": 1.0,
                        "origin": "sense lectura",
                        "data": "2021-06-01",
                        "days": 30,
                        "date_from": "01/06/2021",
                        "date_to": "30/06/2021",
                        "date_to_d": "2021-06-30",
                        "iva": "",
                    },
                ],
            },
        )

    @mock.patch.object(giscedata_facturacio_report, "is_2XTD")
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_atr_price"
    )
    def test__get_sub_component_invoice_details_td_power_data_6_power_lines_6_periods_1_block(
        self, get_atr_price_mock_function, is_2XTD_mock_function
    ):
        get_atr_price_mock_function.return_value = 10.0
        is_2XTD_mock_function.return_value = False

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P1",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P2",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P3",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P4",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P5",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P6",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        result = self.r_obj.get_sub_component_invoice_details_td_power_data(**self.bfp(f_id))
        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "header_multi": 3,
                "showing_periods": ["P1", "P2", "P3", "P4", "P5", "P6"],
                "iva_column": False,
                "power_lines_data": [
                    {
                        "P1": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P2": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P3": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P4": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P5": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P6": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "iva": "",
                        "multi": 1,
                        "days_per_year": 365,
                        "total": 6.0,
                        "origin": "sense lectura",
                        "data": "2021-06-01",
                        "days": 30,
                        "date_from": "01/06/2021",
                        "date_to": "30/06/2021",
                        "date_to_d": "2021-06-30",
                    },
                ],
            },
        )

    @mock.patch.object(giscedata_facturacio_report, "is_2XTD")
    @mock.patch.object(
        giscedata_facturacio_report.GiscedataFacturacioFacturaReport, "get_atr_price"
    )
    def test__get_sub_component_invoice_details_td_power_data_12_power_lines_6_periods_2_block(
        self, get_atr_price_mock_function, is_2XTD_mock_function
    ):
        get_atr_price_mock_function.return_value = 10.0
        is_2XTD_mock_function.return_value = False

        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P1",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-05-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P2",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-05-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P3",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-05-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P4",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-05-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P5",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-05-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P6",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "extra": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 0,
                "account_id": 1,
                "data_desde": "2021-05-01",
                "data_fins": "2021-05-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P1",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 1,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P2",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 1,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P3",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 1,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P4",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 1,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P5",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 1,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        self.linia_f_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "P6",
                "quantity": 1.0,
                "price_subtotal": 10.0,
                "price_unit_multi": 1,
                "price_unit": 1,
                "multi": 1,
                "factura_id": f_id,
                "tipus": "potencia",
                "product_id": 1,
                "account_id": 1,
                "data_desde": "2021-06-01",
                "data_fins": "2021-06-30",
            },
        )

        result = self.r_obj.get_sub_component_invoice_details_td_power_data(**self.bfp(f_id))

        self.assertYamlfy(result)
        self.assertEquals(
            result,
            {
                "header_multi": 6,
                "showing_periods": ["P1", "P2", "P3", "P4", "P5", "P6"],
                "iva_column": False,
                "power_lines_data": [
                    {
                        "P1": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P2": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P3": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P4": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P5": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P6": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "multi": 1,
                        "days_per_year": 365,
                        "total": 6.0,
                        "origin": "sense lectura",
                        "data": "2021-05-01",
                        "days": 30,
                        "date_from": "01/05/2021",
                        "date_to": "30/05/2021",
                        "date_to_d": "2021-05-30",
                        "iva": "",
                    },
                    {
                        "P1": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P2": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P3": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P4": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P5": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "P6": {
                            "extra": 1.0,
                            "price_unit": 1.0,
                            "price_subtotal": 1.0,
                            "price_unit_multi": 1.0,
                            "atr_price": 10.0,
                            "quantity": 1.0,
                        },
                        "multi": 1,
                        "days_per_year": 365,
                        "total": 6.0,
                        "origin": "sense lectura",
                        "data": "2021-06-01",
                        "days": 30,
                        "date_from": "01/06/2021",
                        "date_to": "30/06/2021",
                        "date_to_d": "2021-06-30",
                        "iva": "",
                    },
                ],
            },
        )
