# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from .. import giscedata_polissa
import mock


class PolissaLecturesCalculadesTest(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "retrocedir_lot")
    @mock.patch.object(
        giscedata_polissa.GiscedataPolissaCalculada, "_check_conditions_polissa_calculades"
    )
    def test_crear_lectures_calculades__sense_lectures(
        self, mock_check_conditions_polissa_calculades, mock_retrocedir_lot
    ):

        imd_obj = self.model("ir.model.data")
        pol_obj = self.model("giscedata.polissa")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

        check_conditions_values = [(False, u"no té categoria"), (False, u"no es 2.0TD")]

        def check_conditions_polissa_calculades(cursor, uid, polissa_id, context={}):
            return check_conditions_values.pop()

        mock_check_conditions_polissa_calculades.side_effect = check_conditions_polissa_calculades
        mock_retrocedir_lot.return_value = None

        result = pol_obj.crear_lectures_calculades(
            self.cursor, self.uid, [polissa_id, polissa_id], {}
        )

        self.assertEqual(
            result[0], u"La pòlissa 0001C no compleix les condicions perquè no es 2.0TD"
        )
        self.assertEqual(
            result[1], u"La pòlissa 0001C no compleix les condicions perquè no té categoria"
        )
        self.assertEqual(len(result), 2)

    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "retrocedir_lot")
    @mock.patch.object(
        giscedata_polissa.GiscedataPolissaCalculada, "_check_conditions_polissa_calculades"
    )
    def test_crear_lectures_calculades__sense_data_ultima_lectura(
        self, mock_check_conditions_polissa_calculades, mock_retrocedir_lot
    ):

        imd_obj = self.model("ir.model.data")
        pol_obj = self.model("giscedata.polissa")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

        mock_check_conditions_polissa_calculades.return_value = (True, u"Ok")
        mock_retrocedir_lot.return_value = None

        pol_obj.write(self.cursor, self.uid, polissa_id, {"data_ultima_lectura": None})

        result = pol_obj.crear_lectures_calculades(self.cursor, self.uid, [polissa_id], {})

        self.assertEqual(result[0], u"La pòlissa 0001C sense data ultima lectura")
        self.assertEqual(len(result), 1)

    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "retrocedir_lot")
    @mock.patch.object(
        giscedata_polissa.GiscedataPolissaCalculada, "_check_conditions_polissa_calculades"
    )
    def test_crear_lectures_calculades__data_fi_menor_inicial(
        self, mock_check_conditions_polissa_calculades, mock_retrocedir_lot
    ):

        imd_obj = self.model("ir.model.data")
        pol_obj = self.model("giscedata.polissa")
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

        mock_check_conditions_polissa_calculades.return_value = (True, u"Ok")
        mock_retrocedir_lot.return_value = None

        pol_obj.write(
            self.cursor,
            self.uid,
            polissa_id,
            {"data_ultima_lectura": "2022-03-01", "data_ultima_lectura_f1": "2022-03-02"},
        )

        result = pol_obj.crear_lectures_calculades(self.cursor, self.uid, [polissa_id], {})

        self.assertEqual(
            result[0],
            u"La pòlissa 0001C té lectura F1 amb data {} i data última factura {}.".format(
                "2022-03-02", "2022-03-01"
            ),
        )
        self.assertEqual(len(result), 1)
