# -*- coding: utf-8 -*-
from osv import osv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class GiscedataFacturacioValidationValidator(osv.osv):
    _inherit = 'giscedata.facturacio.validation.validator'
    _name = 'giscedata.facturacio.validation.validator'


    def check_origin_readings_by_contract_category(self, cursor, uid, fact, parameters):

        if 'categoria' not in parameters:
            return None
        
        pcat_obj = self.pool.get('giscedata.polissa.category')
        pcat_ids = pcat_obj.search(cursor, uid,[('name','like','%'+parameters['categoria']+'%')])

        if pcat_ids and pcat_ids[0] in [x.id for x in fact.polissa_id.category_id]:

            lect_obj = self.pool.get('giscedata.lectures.lectura')

            lo_obj = self.pool.get('giscedata.lectures.origen')
            loc_obj = self.pool.get('giscedata.lectures.origen_comer')

            not_alowed_origins_ids = lo_obj.search(cursor, uid,[('codi','in', eval(parameters['lectures_origen_codes']))])
            not_alowed_origins_comer_ids = loc_obj.search(cursor, uid,[('codi','in', eval(parameters['lectures_origen_comer_codes']))])

            data_inici = datetime.strptime(fact.data_inici, '%Y-%m-%d') - timedelta(days=1)

            clause = [
                ('comptador.polissa', '=', fact.polissa_id.id),
                ('comptador.active', '=', True),
                ('tipus', '=', 'A'),
                ('name', '>=', data_inici.strftime('%Y-%m-%d')),
                ('name', '<=', fact.data_final),
            ]
            if not_alowed_origins_ids:
                clause.append(('origen_id', 'in', not_alowed_origins_ids))
            if not_alowed_origins_comer_ids:
                clause.append(('origen_comer_id', 'in', not_alowed_origins_comer_ids))

            lectures_ids = lect_obj.q(cursor, uid).read(
                ['id', 'name', 'origen_id', 'origen_comer_id'], order_by=['name.asc']
            ).where(clause)

            if len(lectures_ids) == 0:
                return None

            origen_id = list(set([x['origen_id']for x in lectures_ids]))
            origen_comer_id = list(set([x['origen_comer_id']for x in lectures_ids]))

            origins = [x['name'] for x in lo_obj.read(cursor, uid, origen_id, ['name'])]
            origins_comer = [x['name'] for x in loc_obj.read(cursor, uid, origen_comer_id, ['name'])]

            return {
                'categoria': parameters['categoria'],
                'origen': ','.join(origins),
                'origen_distri': ','.join(origins_comer)
            }

        return None

    def check_min_periods_and_teoric_maximum_consum(self, cursor, uid, fact, parameters):

        if 'category' not in parameters:
            return None

        pcat_obj = self.pool.get('giscedata.polissa.category')
        pcat_ids = pcat_obj.search(cursor, uid,[('name','like','%'+parameters['category']+'%')])

        if pcat_ids and pcat_ids[0] in [x.id for x in fact.polissa_id.category_id]:

            fact_obj = self.pool.get('giscedata.facturacio.factura')

            pol_obj = self.pool.get('giscedata.polissa')
            teoric_maximum_consume_GC = pol_obj.read(cursor, uid, fact.polissa_id.id, ['teoric_maximum_consume_GC'])['teoric_maximum_consume_GC']

            n_months = parameters['n_months']
            min_periods = parameters.get('min_periods', False)
            to_date = datetime.strptime(fact.data_inici, '%Y-%m-%d')
            from_date = to_date - relativedelta(months=n_months)

            context = {}
            if parameters.get("min_invoice_len"):
                context['min_invoice_len'] = parameters.get("min_invoice_len")

            parameter_by_date = fact_obj.get_parameter_by_contract(
                cursor, uid, fact.polissa_id.id, 'energia_kwh', from_date,
                to_date, min_periods, context=context
            )

            max_consume = False
            number_of_invoices = len(parameter_by_date)
            if number_of_invoices > 0:
                max_consume = max(parameter_by_date.values())

            if (not max_consume or number_of_invoices < n_months) and (not teoric_maximum_consume_GC or teoric_maximum_consume_GC == 0):
                return {
                    'invoice_consume': fact.energia_kwh,
                }

        return None

    def check_consume_by_percentage_and_category(self, cursor, uid, fact, parameters):

        if 'category' not in parameters:
            return None

        pcat_obj = self.pool.get('giscedata.polissa.category')
        pcat_ids = pcat_obj.search(cursor, uid,[('name','like','%'+parameters['category']+'%')])

        if pcat_ids and pcat_ids[0] in [x.id for x in fact.polissa_id.category_id]:

            fact_obj = self.pool.get('giscedata.facturacio.factura')


            if parameters.get('min_amount', False) and abs(fact.amount_total) <= parameters.get('min_amount', 0.0):
                return None

            n_months = parameters['n_months']
            min_periods = parameters.get('min_periods', False)
            to_date = datetime.strptime(fact.data_inici, '%Y-%m-%d')
            from_date = to_date - relativedelta(months=n_months)

            context = {}
            if parameters.get("min_invoice_len"):
                context['min_invoice_len'] = parameters.get("min_invoice_len")

            parameter_by_date = fact_obj.get_parameter_by_contract(
                cursor, uid, fact.polissa_id.id, 'energia_kwh', from_date,
                to_date, min_periods, context=context
            )

            max_consume = False
            number_of_invoices = len(parameter_by_date)
            if number_of_invoices > 0:
                max_consume = max(parameter_by_date.values())

            pol_obj = self.pool.get('giscedata.polissa')
            teoric_maximum_consume_GC = pol_obj.read(cursor, uid, fact.polissa_id.id, ['teoric_maximum_consume_GC'])['teoric_maximum_consume_GC']

            if not max_consume or number_of_invoices < n_months:
                max_consume = False

            if not max_consume and teoric_maximum_consume_GC and teoric_maximum_consume_GC > 0:
                max_consume = teoric_maximum_consume_GC

            if max_consume:
                percentage_margin = parameters['overuse_percentage']

                inv_consume = fact.energia_kwh
                if inv_consume > (max_consume * (100.0 + percentage_margin))/100.0:
                    return {
                        'invoice_consume': inv_consume,
                        'percentage': percentage_margin,
                        'maximum_consume': max_consume,
                        'n_months': n_months,
                        'maximum_teoric_consume_GC': teoric_maximum_consume_GC if teoric_maximum_consume_GC else 0,
                    }

        return None

    def check_consume_by_percentage(self, cursor, uid, fact, parameters):

        pcat_obj = self.pool.get('giscedata.polissa.category')
        pcat_ids = pcat_obj.search(cursor, uid,[('name','like','%Gran Contracte%')])

        if pcat_ids and pcat_ids[0] in [x.id for x in fact.polissa_id.category_id]:
            return None

        return super(GiscedataFacturacioValidationValidator,
            self).check_consume_by_percentage(cursor, uid, fact, parameters)

    def check_consume_by_amount(self, cursor, uid, fact, parameters):

        pcat_obj = self.pool.get('giscedata.polissa.category')
        pcat_ids = pcat_obj.search(cursor, uid,[('name','like','%%Gran Contracte%')])

        if pcat_ids and pcat_ids[0] in [x.id for x in fact.polissa_id.category_id]:
            return None

        return super(GiscedataFacturacioValidationValidator,
            self).check_consume_by_amount(cursor, uid, fact, parameters)

    def check_gkwh_G_invoices(self, cursor, uid, clot, data_inici,
                                    data_fi, parametres={}):
        modcon_obj = self.pool.get('giscedata.polissa.modcontractual')
        compta_obj = self.pool.get('giscedata.lectures.comptador')
        facturador_obj = self.pool.get('giscedata.facturacio.facturador')
        imd_obj = self.pool.get('ir.model.data')
        origen_comer_f1g_id = imd_obj.get_object_reference(cursor, uid, 'giscedata_facturacio_switching', 'origen_comer_f1_g')[1]
        polissa = clot.polissa_id
        if not polissa.te_assignacio_gkwh:
            return None

        data_inici, data_final = polissa.get_inici_final_a_facturar(
            use_lot=clot.lot_id.id, context={'validacio': True}
        )
        intervals = polissa.get_modcontractual_intervals(data_inici, data_final)
        mod_ids = []
        mod_dates = {}
        for mod_data in sorted(intervals.keys()):
            mod_id = intervals[mod_data]['id']
            mod_ids.append(mod_id)
            mod_dates[mod_id] = intervals[mod_data]['dates']

        for modcontractual in modcon_obj.browse(cursor, uid, mod_ids):
            mod_id = modcontractual.id
            tid = modcontractual.tarifa.id
            data_inici_periode_f = max(data_inici, mod_dates[mod_id][0])
            data_final_periode_f = min(data_final, mod_dates[mod_id][1])
            reparto_real = facturador_obj.reparto_real(cursor, uid, modcontractual.tarifa.name)
            if modcontractual.polissa_id.active and len(mod_ids) == 1:
                data_final_periode_f = data_final
            c_actius = polissa.comptadors_actius(data_inici_periode_f,
                data_final_periode_f, order='data_alta asc')

            for compt in compta_obj.browse(cursor, uid, c_actius):
                # El métode get_inici_final_a_facturar no té en compte que la
                # lectura inicial de la pólissa/modcon comença el dia anterior a
                # l'activació. Per tant ara restem 1 dia a les dates que estem
                # utilitzant
                data_inici_periode_f2 = (datetime.strptime(data_inici_periode_f, "%Y-%m-%d") - timedelta( days=1)).strftime("%Y-%m-%d")
                ctx = {
                    'fins_lectura_fact': data_final,
                    'ult_lectura_fact': data_inici_periode_f2
                }
                if reparto_real:
                    lectures_activa = compt.get_lectures_month_per_facturar(
                        tid, 'A', context=ctx
                    )
                else:
                    lectures_activa = compt.get_lectures_per_facturar(
                        tid, 'A', context=ctx
                    )

                for periode, lectura in lectures_activa.items():
                    if lectura['actual']['origen_comer_id'][0] == origen_comer_f1g_id:
                        return True

        return None


GiscedataFacturacioValidationValidator()
