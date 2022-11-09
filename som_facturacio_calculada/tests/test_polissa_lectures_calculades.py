# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from expects import *
from datetime import datetime, timedelta
import osv
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
    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "_check_conditions_polissa_calculades")
    def test_crear_lectures_calculades__sense_lectures(self, mock_check_conditions_polissa_calculades, mock_retrocedir_lot):

        imd_obj = self.model('ir.model.data')
        pol_obj = self.model('giscedata.polissa')
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        check_conditions_values = [(False,u'no té categoria'),(False,u'no es 2.0TD')]
        def check_conditions_polissa_calculades(cursor, uid, polissa_id, context={}):
            return check_conditions_values.pop()
        mock_check_conditions_polissa_calculades.side_effect = check_conditions_polissa_calculades
        mock_retrocedir_lot.return_value = None

        result = pol_obj.crear_lectures_calculades(self.cursor, self.uid, [polissa_id, polissa_id], {})

        self.assertEqual(result[0], u'La pòlissa 0001C no compleix les condicions per que no es 2.0TD')
        self.assertEqual(result[1], u'La pòlissa 0001C no compleix les condicions per que no té categoria')
        self.assertEqual(len(result), 2)


    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "retrocedir_lot")
    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "_check_conditions_polissa_calculades")
    def test_crear_lectures_calculades__sense_data_ultima_lectura(self, mock_check_conditions_polissa_calculades, mock_retrocedir_lot):

        imd_obj = self.model('ir.model.data')
        pol_obj = self.model('giscedata.polissa')
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        mock_check_conditions_polissa_calculades.return_value = (True,u'Ok')
        mock_retrocedir_lot.return_value = None

        pol_obj.write(self.cursor, self.uid, polissa_id, {'data_ultima_lectura': None})

        result = pol_obj.crear_lectures_calculades(self.cursor, self.uid, [polissa_id], {})

        self.assertEqual(result[0], u'La pòlissa 0001C sense data ultima lectura')
        self.assertEqual(len(result), 1)


    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "retrocedir_lot")
    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "_check_conditions_polissa_calculades")
    def test_crear_lectures_calculades__data_fi_menor_inicial(self, mock_check_conditions_polissa_calculades, mock_retrocedir_lot):

        imd_obj = self.model('ir.model.data')
        pol_obj = self.model('giscedata.polissa')
        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        mock_check_conditions_polissa_calculades.return_value = (True,u'Ok')
        mock_retrocedir_lot.return_value = None

        pol_obj.write(self.cursor, self.uid, polissa_id, {'data_ultima_lectura': '2022-03-01', 'data_ultima_lectura_f1':  '2022-03-02' })

        result = pol_obj.crear_lectures_calculades(self.cursor, self.uid, [polissa_id], {})

        self.assertEqual(result[0], u'La pòlissa 0001C té lectura F1 amb data {} i data última factura {}.'.format('2022-03-02','2022-03-01'))
        self.assertEqual(len(result), 1)

    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "retrocedir_lot")
    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "check_conditions_lectures_calculades")
    def test_crear_lectures_calculades__polissa_sense_comptadors(self, mock_check_conditions_lectures_calculades, mock_retrocedir_lot):

        imd_obj = self.model('ir.model.data')
        pol_obj = self.model('giscedata.polissa')
        mtr_o = self.model('giscedata.lectures.comptador')

        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        mock_check_conditions_lectures_calculades.return_value = (True,u'Ok')
        mock_retrocedir_lot.return_value = None

        pol_obj.write(self.cursor, self.uid, polissa_id, {'data_ultima_lectura': '2022-03-02', 'data_ultima_lectura_f1':  '2022-03-01',  })

        mtr_ids = mtr_o.search(self.cursor, self.uid, [
                ('polissa.id', '=', polissa_id),
                ('active', '=', True)
            ])

        mtr_o.write(self.cursor, self.uid, mtr_ids, {'active': False})

        result = pol_obj.crear_lectures_calculades(self.cursor, self.uid, [polissa_id], {})

        self.assertEqual(result[0], u"La pòlissa 0001C no té comptador actiu")
        self.assertEqual(len(result), 1)

    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "retrocedir_lot")
    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "check_conditions_lectures_calculades")
    def test_crear_lectures_calculades__polissa_multi_comptadors(self, mock_check_conditions_lectures_calculades, mock_retrocedir_lot):

        imd_obj = self.model('ir.model.data')
        pol_obj = self.model('giscedata.polissa')
        mtr_o = self.model('giscedata.lectures.comptador')

        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        mock_check_conditions_lectures_calculades.return_value = (True,u'Ok')
        mock_retrocedir_lot.return_value = None

        pol_obj.write(self.cursor, self.uid, polissa_id, {'data_ultima_lectura': '2022-03-02', 'data_ultima_lectura_f1':  '2022-03-01',  })

        mtr_ids = mtr_o.search(self.cursor, self.uid, [
                ('polissa.id', '=', polissa_id),
                ('active', '=', True)
            ])

        if len(mtr_ids) == 1:
            mtr_o.create(self.cursor, self.uid, {'polissa': polissa_id, 'active': True, 'name': '0001C'})

        result = pol_obj.crear_lectures_calculades(self.cursor, self.uid, [polissa_id], {})

        self.assertEqual(result[0], u"La pòlissa 0001C té multiples comptadors actius")
        self.assertEqual(len(result), 1)

    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "retrocedir_lot")
    @mock.patch.object(giscedata_polissa.GiscedataPolissaCalculada, "check_conditions_lectures_calculades")
    def test_crear_lectures_calculades__lect_calc_major_en21d_nocalc(self, mock_check_conditions_lectures_calculades, mock_retrocedir_lot):

        def add_days(the_date, d):
            return (datetime.strptime(the_date, '%Y-%m-%d') + timedelta(days=d)).strftime("%Y-%m-%d")

        imd_obj = self.model('ir.model.data')
        pol_obj = self.model('giscedata.polissa')
        mtr_o = self.model('giscedata.lectures.comptador')
        lects_o = self.model('giscedata.lectures.lectura')

        polissa_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        lc_origin = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_facturacio_calculada', 'origen_lect_calculada'
        )[1]

        mock_check_conditions_lectures_calculades.return_value = (True,u'Ok')
        mock_retrocedir_lot.return_value = None
        pol_obj.write(self.cursor, self.uid, polissa_id, {'data_ultima_lectura': '2000-03-02', 'data_ultima_lectura_f1':  '2000-03-01',  })
        mtr_ids = mtr_o.search(self.cursor, self.uid, [
                ('polissa.id', '=', polissa_id),
                ('active', '=', True)
            ])

        mtr_id = mtr_ids[0]
        mtr = mtr_o.browse(self.cursor, self.uid, mtr_id)

        ultima_lectura_lectures_data = mtr.lectures[0].name
        ultima_lectura_factura_21_data = add_days('2000-03-01', 21)

        lect_ids = [a.id for a in mtr.lectures]
        lects_o.write(self.cursor, self.uid, lect_ids, {'origen_id': lc_origin})

        result = pol_obj.crear_lectures_calculades(self.cursor, self.uid, [polissa_id], {})
        self.assertEqual(result[0], u"La pòlissa {}, data de lectura calculada ({}) igual o major a data d'ultima factura no calculada + 21 ({})".format(
                        '0001C',
                        ultima_lectura_lectures_data,
                        ultima_lectura_factura_21_data))
        self.assertEqual(len(result), 1)