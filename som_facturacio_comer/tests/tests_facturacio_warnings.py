# -*- coding: utf-8 -*-
from expects import expect
from expects import contain
from destral import testing
from destral.transaction import Transaction
from expects import expect
from expects import raise_error
from expects import equal
from expects import contain
from expects import contain_exactly
import json

class TestsFacturesValidation(testing.OOTestCase):
    def setUp(self):
        fact_obj = self.openerp.pool.get('giscedata.facturacio.factura')
        line_obj = self.openerp.pool.get('giscedata.facturacio.factura.linia')
        warn_obj = self.openerp.pool.get(
            'giscedata.facturacio.validation.warning.template'
        )
        self.txn = Transaction().start(self.database)

        cursor = self.txn.cursor
        uid = self.txn.user

        ctx = {'active_test': False}

        # We make sure that all warnings are active
        warn_ids = warn_obj.search(
            cursor, uid, [], context=ctx
        )
        warn_obj.write(cursor, uid, warn_ids, {'active': True})

    def tearDown(self):
        self.txn.stop()

    def activate_contract(self, contract_id):
        polissa_obj = self.model('giscedata.polissa')

        polissa_obj.send_signal(self.txn.cursor, self.txn.user, contract_id, ['validar', 'contracte'])

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_fixture(self, model, reference):
        imd_obj = self.model('ir.model.data')
        return imd_obj.get_object_reference(
            self.txn.cursor, self.txn.user,
            model,
            reference
        )[1]

    def validation_warnings(self, factura_id):
        vali_obj = self.model('giscedata.facturacio.validation.validator')
        warn_obj = self.model('giscedata.facturacio.validation.warning')
      
        warning_ids = vali_obj.validate_invoice(
            self.txn.cursor, self.txn.user,
            factura_id
        )
        warning_vals = warn_obj.read(
            self.txn.cursor, self.txn.user,
            warning_ids,
            ['name']
        )
        return [warn['name'] for warn in warning_vals]

    # Scenario contruction helpers
    def prepare_contract(self, pol_id, data_alta, data_ultima_lectura):
        contract_obj = self.model('giscedata.polissa')
        cursor = self.txn.cursor
        uid = self.txn.user

        vals = {
            'data_alta': data_alta,
            'data_baixa': False,
            'data_ultima_lectura': data_ultima_lectura,
            'facturacio': 1,
            'facturacio_potencia': 'icp',
            'tg': '1',
            'lot_facturacio': False
        }
        contract_obj.write(cursor, uid, pol_id, vals)
        contract_obj.send_signal(cursor, uid, [pol_id], [
            'validar', 'contracte'
        ])
        contract = contract_obj.browse(cursor, uid, pol_id)
        for meter in contract.comptadors:
            for l in meter.lectures:
                l.unlink(context={})
            for lp in meter.lectures_pot:
                lp.unlink(context={})
            meter.write({'lloguer': False})
        return contract.comptadors[0].id

    def create_category_to_contract_by_name(self, pol_id, category_name):
        pol_obj = self.model('giscedata.polissa')
        pcat_obj = self.model('giscedata.polissa.category')
        cursor = self.txn.cursor
        uid = self.txn.user

        pcat_ids = pcat_obj.search(cursor, uid, [('name','like','%'+category_name+'%')])
        if pcat_ids:
            pcat_id = pcat_ids[0]
        else:
            pcat_id = pcat_obj.create(cursor, uid, {
                'name': category_name,
                'code': 'ZZ',
            })
        pol_obj.write(cursor, uid, pol_id, {'category_id': [(4, pcat_id)]})

    def create_measure(self, meter_id, date_measure, measure, origen_code, origen_comer_code):
        measure_obj = self.model('giscedata.lectures.lectura')
        lo_obj = self.model('giscedata.lectures.origen')
        loc_obj = self.model('giscedata.lectures.origen_comer')
        periode_id = self.get_fixture('giscedata_polissa', 'p1_e_tarifa_20A_new')
        origins_ids = lo_obj.search(self.txn.cursor, self.txn.user, [('codi','=', origen_code)]) if origen_code else []
        origins_comer_ids = loc_obj.search(self.txn.cursor, self.txn.user, [('codi','=', origen_comer_code)]) if origen_code else []

        vals = {
            'name': date_measure,
            'periode': periode_id,
            'lectura': measure,
            'tipus': 'A',
            'comptador': meter_id,
            'observacions': '',
        }
        if origins_ids:
            vals['origen_id'] = origins_ids[0]
        if origins_comer_ids:
            vals['origen_comer_id'] = origins_comer_ids[0]
        
        return measure_obj.create(self.txn.cursor, self.txn.user, vals)

    def modify_invoice(self, fact_id, pol_id, start, end, amount=1):
        fact_obj = self.model('giscedata.facturacio.factura')

        fact_obj.write(
            self.txn.cursor, self.txn.user, fact_id, {
                'data_inici': start,
                'data_final': end,
                'polissa_id': pol_id,
                'state': 'open',
                'type': 'out_invoice',
                'energia_kwh': amount,
            }
        )

    def crear_modcon(self, polissa_id, teoric_max, ini, fi):
        cursor = self.txn.cursor
        uid = self.txn.user
        pool = self.openerp.pool
        polissa_obj = pool.get('giscedata.polissa')

        pol = polissa_obj.browse(cursor, uid, polissa_id)
        pol.send_signal(['modcontractual'])
        polissa_obj.write(cursor, uid, polissa_id, {'teoric_maximum_consume_GC': teoric_max})
        wz_crear_mc_obj = pool.get('giscedata.polissa.crear.contracte')

        ctx = {'active_id': polissa_id}
        params = {'duracio': 'nou'}

        wz_id_mod = wz_crear_mc_obj.create(cursor, uid, params, ctx)
        wiz_mod = wz_crear_mc_obj.browse(cursor, uid, wz_id_mod, ctx)
        res = wz_crear_mc_obj.onchange_duracio(
            cursor, uid, [wz_id_mod], wiz_mod.data_inici, wiz_mod.duracio,
            ctx
        )
        wiz_mod.write({
            'data_inici': ini,
            'data_final': fi
        })
        wiz_mod.action_crear_contracte(ctx)

    def create_inv_line(self, inv_id, quantity):
        cursor = self.txn.cursor
        uid = self.txn.user
        pool = self.openerp.pool
        linia_obj = pool.get('giscedata.facturacio.factura.linia')

        linia_id = linia_obj.create(cursor, uid, {
            'name': 'Linia 1',
            'tipus': 'energia',
            'price_unit': 1,
            'factura_id': inv_id,
            'product_id': False,
            'account_id': 1,
            'quantity': quantity,
        })

    def test_check_origin_readings_by_contract_category__contract_without_category(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        self.create_measure(meter_id,'2017-02-18',8000,'40','F1')
        self.create_measure(meter_id,'2017-03-17',8600,'40','F1')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain('SF01'))

    def test_check_origin_readings_by_contract_category__contract_with_wrong_category(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        self.create_category_to_contract_by_name(pol_id,'Petit Contracte')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        self.create_measure(meter_id,'2017-02-18',8000,'40','F1')
        self.create_measure(meter_id,'2017-03-17',8600,'40','F1')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain('SF01'))

    def test_check_origin_readings_by_contract_category__contract_with_category_readings_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        self.create_category_to_contract_by_name(pol_id,'Gran Contracte')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        self.create_measure(meter_id,'2017-02-18',8000,'40','Q1')
        self.create_measure(meter_id,'2017-03-17',8600,'40','Q1')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain('SF01'))

    def test_check_origin_readings_by_contract_category__contract_with_category_all_readings_not_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        self.create_category_to_contract_by_name(pol_id,'Gran Contracte')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        self.create_measure(meter_id,'2017-02-18',8000,'40','F1')
        self.create_measure(meter_id,'2017-03-17',8600,'40','F1')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).to(contain('SF01'))

    def test_check_origin_readings_by_contract_category__contract_with_category_one_reading_not_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        self.create_category_to_contract_by_name(pol_id,'Gran Contracte')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        self.create_measure(meter_id,'2017-02-18',8000,'40','F1')
        self.create_measure(meter_id,'2017-03-17',8600,'30','Q1')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).to(contain('SF01'))

    def test_check_min_periods_and_teoric_maximum_consum__contract_without_category(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain('SF02'))

    def test_check_min_periods_and_teoric_maximum_consum__contract_with_wrong_category(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        self.create_category_to_contract_by_name(pol_id,'Petit Contracte')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain('SF02'))

    def test_check_min_periods_and_teoric_maximum_consum__contract_with_category_not_periods_not_teoric(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        self.create_category_to_contract_by_name(pol_id,'Gran Contracte')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).to(contain('SF02'))

    def test_check_min_periods_and_teoric_maximum_consum__contract_with_category_and_teoric_zero(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        self.create_category_to_contract_by_name(pol_id,'Gran Contracte')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        self.crear_modcon(pol_id, 0, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).to(contain('SF02'))

    def test_check_min_periods_and_teoric_maximum_consum__contract_with_category_and_teoric_ok(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        self.create_category_to_contract_by_name(pol_id,'Gran Contracte')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        self.create_measure(meter_id,'2017-02-18',8000,'40','Q1')
        self.create_measure(meter_id,'2017-03-17',8600,'40','Q1')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        self.crear_modcon(pol_id, 500, '2017-02-18', '2018-02-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain('SF02'))

    def test_check_consume_by_percentage_and_category__contract_without_category(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain('SF03'))

    def test_check_consume_by_percentage_and_category__contract_with_wrong_category(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        self.create_category_to_contract_by_name(pol_id,'Petit Contracte')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain('SF03'))

    def test_check_consume_by_percentage_and_category__contract_with_category_and_teoric_consumption(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        self.create_category_to_contract_by_name(pol_id,'Gran Contracte')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        inv_id = self.get_fixture('giscedata_facturacio', 'factura_0001')
        self.modify_invoice(inv_id, pol_id, '2017-02-18', '2017-03-17')
        self.create_inv_line(inv_id, 200)
        self.crear_modcon(pol_id, 5, '2017-02-18', '2018-02-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).to(contain('SF03'))

    def test_check_gkwh_G_invoices__contract_without_generationkWh(self):
        pol_id = self.get_fixture('giscedata_polissa', 'polissa_0001')
        meter_id  = self.prepare_contract(pol_id,'2017-01-01','2017-02-18')
        self.crear_modcon(pol_id, 5, '2017-02-18', '2018-02-17')
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain('SV01'))


    def test_validation_V008_lot(self):
        cursor = self.cursor
        uid = self.user

        _, periode_id = self.imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'p1_e_tarifa_20A_new'
        )

        _, origen_id = self.imd_obj.get_object_reference(
            cursor, uid, 'giscedata_lectures', 'origen10'
        )

        _, cnt_lot_id = self.imd_obj.get_object_reference(
            cursor, uid, 'giscedata_facturacio', 'cont_lot_0002'
        )
        _, demo_contract_id = self.imd_obj.get_object_reference(
            cursor, uid, 'giscedata_polissa', 'polissa_0002'
        )
        # Ens assegurem de que l'unic comptador de la polissa tingui
        # lectures. Per forçar la validació, fem que sigui zero totes dues.
        polissa = self.pol_obj.browse(cursor, uid, demo_contract_id)

        if len(polissa.comptadors) != 1:
            raise NotImplementedError

        comptador = polissa.comptadors[0]
        origen_id = self.imd_obj.get_object_reference(
            cursor, uid, 'giscedata_lectures', 'origen10'
        )[1]
        lectura_cv = {
            'periode': periode_id,              'name': '2016-01-02',
            'comptador': comptador.id,          'origen_id': origen_id,
            'tipus': 'A',                       'lectura': 0,
        }
        self.lectures_obj.create(cursor, uid, lectura_cv)
        lectura_cv['name'] = '2016-01-25'
        self.lectures_obj.create(cursor, uid, lectura_cv)

        # We remove other lot_contracts associated with out invoicing lot
        lot_id = self.cnt_lot_obj.read(
            cursor, uid, cnt_lot_id, ['lot_id']
        )['lot_id'][0]
        cnt_lot_to_remove = self.lot_obj.read(
            cursor, uid, lot_id, ['contracte_lot_ids']
        )['contracte_lot_ids']

        cnt_lot_to_remove.remove(cnt_lot_id)
        self.cnt_lot_obj.unlink(cursor, uid, cnt_lot_to_remove)

        # Let's validate the contract
        self.pol_obj.send_signal(
            cursor, uid, [demo_contract_id], ['validar', 'contracte']
        )

        # Next step, we want to validate the lot and the V008 should pop
        self.cnt_lot_obj.validate_individual(cursor, uid, [cnt_lot_id])
        lot_status = self.cnt_lot_obj.read(
            cursor, uid, cnt_lot_id, ['status']
        )['status']
        expect(lot_status).not_to(contain('SV01'))
