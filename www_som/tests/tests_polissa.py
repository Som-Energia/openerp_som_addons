# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction

from datetime import date,datetime,timedelta

class TestPolissaWwwAutolectura(testing.OOTestCase):

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_fixture(self, model, reference):
        return self.imd_obj.get_object_reference(
            self.cursor, self.uid,
            model,
            reference
        )[1]

    def setUp(self):
        self.pol_obj = self.model('giscedata.polissa')
        self.pool_lect_obj = self.model('giscedata.lectures.lectura.pool')
        self.fact_lect_obj = self.model('giscedata.lectures.lectura')
        self.meter_obj = self.model('giscedata.lectures.comptador')
        self.period_obj = self.model('giscedata.polissa.tarifa.periodes')
        self.origin_comer_obj = self.model('giscedata.lectures.origen_comer')
        self.origin_obj = self.model('giscedata.lectures.origen')
        self.tarif_obj = self.model('giscedata.polissa.tarifa')
        self.imd_obj = self.model('ir.model.data')

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    # Helper functions
    def create_lect_pool(self,pol_id,
        date,period,lect_type,value,observations,origen_comer_code,origin_code):
        return self.create_lect(
            pol_id,
            date,
            period,
            lect_type,
            value,
            observations,
            origen_comer_code,
            origin_code,
            True)

    def create_lect_fact(self,pol_id,
        date,period,lect_type,value,observations,origen_comer_code,origin_code):
        return self.create_lect(
            pol_id,
            date,
            period,
            lect_type,
            value,
            observations,
            origen_comer_code,
            origin_code,
            False)

    def create_lect(self,pol_id,
        date,period,lect_type,value,observations,origen_comer_code,origin_code,pool):
        # avaliable codes for origin_comer_code
        # ['Q1','F1','MA','OV','AL','ES','AT','CC']

        # available codes for origin_code
        # ['10','20','30','40','50','99','40','40','60']

        pol_val = self.pol_obj.read(
            self.cursor, self.uid, pol_id, ['comptador', 'tarifa'])
        if not pol_val:
            return None

        meter_search = [
            ('polissa.id', '=', pol_id),
            ('name', '=', pol_val['comptador'])]
        meter_ids = self.meter_obj.search(
            self.cursor, self.uid,meter_search)
        if not meter_ids:
            return None

        period_search = [
            ('tarifa.id', '=', pol_val['tarifa'][0]),
            ('tipus', '=', 'te'),
            ('agrupat_amb', '=', False),
            ('name', '=', period)]
        period_ids = self.period_obj.search(
            self.cursor, self.uid, period_search)
        if not period_ids:
            return None

        origin_comer_ids = self.origin_comer_obj.search(
            self.cursor, self.uid,
            [('codi', '=', origen_comer_code)])
        if not origin_comer_ids:
            return None

        origin_id = self.origin_obj.search(
            self.cursor, self.uid,
            [('codi', '=', origin_code)])[0]

        vals = {'comptador': meter_ids[0],
            'name': date,
            'periode': period_ids[0],
            'tipus': lect_type,
            'lectura': value,
            'observacions': observations,
            'origen_comer_id': origin_comer_ids[0],
            'origen_id': origin_id,
            }
        if pool:
            return self.pool_lect_obj.create(self.cursor,self.uid,vals)
        else:
            return self.fact_lect_obj.create(self.cursor,self.uid,vals)

    def change_polissa_power_method(self, pol_id, method):
        self.pol_obj.write(self.cursor, self.uid,
            pol_id, {'facturacio_potencia': method})

    def test_www_ultimes_lectures_reals_retorna_reals_i_estimades(self):
        pol_obj = self.openerp.pool.get('giscedata.polissa')
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0002')
        test_date = date.today() - timedelta(days=1)
        self.change_polissa_power_method(pol_id, 'icp')

        a = self.create_lect_pool(
            pol_id, str(test_date), 'P1', 'A', 22287, 'test', 'OV', '50')

        b = self.create_lect_pool(
            pol_id, str(test_date-timedelta(days=31)), 'P1', 'A', 33387, 'test', 'OV', '40')

        c = self.create_lect_pool(
            pol_id, str(test_date-timedelta(days=61)), 'P1', 'A', 99987, 'test', 'OV', '99')

        res = pol_obj.www_ultimes_lectures_reals(self.cursor, self.uid, pol_id)
        kw_lects = [i['lectura'] for i in res]

        self.assertIn(22287, kw_lects)
        self.assertIn(33387, kw_lects)
        self.assertNotIn(99987, kw_lects)

        # Test origen correcto
        for lectura in res:
            if lectura['lectura'] == 22287:
                self.assertEqual(lectura['origen'], 'Autolectura')
            elif lectura['lectura'] == 33387:
                self.assertEqual(lectura['origen'], 'Distribuidora (Estimada)')
