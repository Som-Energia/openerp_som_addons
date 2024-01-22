# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from osv import osv


class GiscedataFacturacioSwitchingValidator(osv.osv):

    _name = 'giscedata.facturacio.switching.validator'
    _inherit = 'giscedata.facturacio.switching.validator'

    def check_consum_lectures_facturat_incoherent(self, cursor, uid, line, f1, parameters=None):
        if not parameters:
            parameters = {}
        errors = []
        consume_lect_period = []
        lect_helper = self.pool.get('giscedata.lectures.switching.helper')
        polissa_obj = self.pool.get('giscedata.polissa')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        for fact_xml in f1.facturas_atr:
            # Les de lectura en baixa no cuadrarà el mesurat amb el facturat,
            # per tant no ho podem comprovar
            if fact_xml.datos_factura.marca_medida_con_perdidas == 'S':
                continue
            # Per les regularitzadores i complementaries tampoc
            if fact_xml.datos_factura.tipo_factura in ["G", "C"]:
                continue
            # per les tarifes noves amb lectures antiues. TODO: podriem aplicar percentatges del BOE i fer el check
            if fact_xml.te_lectures_pre_td_amb_tarifa_td():
                continue
            # Per les anuladores de regularitzadores i complementaries
            if fact_xml.datos_factura.tipo_factura in ('A', 'R'):
                refunded_origin = fact_xml.datos_factura.codigo_factura_rectificada_anulada
                fact_refunded = fact_obj.search(cursor, uid, [
                    ('origin', '=', refunded_origin),
                    ('tipo_rectificadora', 'in', ('C', 'G')),
                ])
                if not fact_refunded:
                    fact_refunded = fact_obj.search(cursor, uid, [
                        ('origin', 'like', '%{}%'.format(refunded_origin)),
                        ('tipo_rectificadora', 'in', ('C', 'G')),
                    ])
                if fact_refunded:
                    continue
            # Per autoconsum tampoc
            if fact_xml.te_autoconsum():
                continue
            # Per els eventuales a tanto alzado tampoc
            if fact_xml.datos_factura.fecha_desde_factura:
                start_date = datetime.strptime(fact_xml.datos_factura.fecha_desde_factura, '%Y-%m-%d')
                start_date += timedelta(days=1)
                data_inici = start_date.strftime('%Y-%m-%d')
                polissa_id = lect_helper.find_polissa_with_cups_id(
                    cursor, uid, line.cups_id.id, data_inici, fact_xml.datos_factura.fecha_hasta_factura
                )
                context = {'date': fact_xml.datos_factura.fecha_hasta_factura, 'from_f1': True, 'avoid_error': True}
                polissa_vals = polissa_obj.read(cursor, uid, polissa_id, ['contract_type'], context=context)
                if polissa_vals['contract_type'] == '09':
                    continue
            for compt_xml in fact_xml.get_comptadors():
                consume_lect_period += self.get_consume_and_period_by_meter(
                    cursor, uid, compt_xml
                )
            consume_by_period = {}
            for c in consume_lect_period:
                period = c['period']
                consume_by_period[period] = consume_by_period.get(period, 0.0) + c['total_consum']

            consums_facturats = dict.fromkeys(consume_by_period.keys(), 0.0)
            for ltype, line_xml in fact_xml.get_linies_factura_by_type().iteritems():
                if ltype == 'energia':
                    result = self.get_consume_by_periode_facturat(
                        cursor, uid, ltype, line_xml
                    )
                    for cf in result:
                        consums_facturats[cf['period']] += cf['total_consum']

            tolerance_by_period = parameters.get('tolerance_by_period', 1.0)
            for period, cons_fact in consums_facturats.items():
                if abs(round(consume_by_period[period], 2) - round(cons_fact, 2)) > tolerance_by_period:
                    errors.append({
                        'period': period,
                        'consum_facturat': cons_fact,
                        'total_consum': consume_by_period[period]
                    })
        return errors

    def get_consume_and_period_by_meter(self, cursor, uid, compt_xml):
        period_consum = []
        for lect_xml in compt_xml.get_lectures(tipus=['A']):
            if lect_xml.periode:
                lect_hasta = float(lect_xml.lectura_hasta.lectura_data.Lectura.text.strip())
                lect_desde = float(lect_xml.lectura_desde.lectura_data.Lectura.text.strip())
                consume = round(lect_hasta - lect_desde, 2)

                if lect_xml.ajuste and lect_xml.ajuste.ajuste_por_integrador:
                    consume += lect_xml.ajuste.ajuste_por_integrador
                if consume < 0:
                    giro = lect_xml.gir_comptador
                    consume += giro

                period_consum.append({
                        'period': lect_xml.periode,
                        'total_consum': consume
                    })
        return period_consum

    def check_f1_foradat(self, cursor, uid, line, f1, parameters=None):
        f1_o = self.pool.get('giscedata.facturacio.importacio.linia')
        lect_helper = self.pool.get('giscedata.lectures.switching.helper')
        polissa_obj = self.pool.get('giscedata.polissa')
        errors = []
        for fact_xml in f1.facturas_atr:
            if not fact_xml.datos_factura.fecha_desde_factura:
                continue  # N'hauria de tenir. Sino vol dir que es de conceptes i no hem de fer res
            if fact_xml.datos_factura.tipo_factura != 'N':
                continue
            # Primer mirem si el contracte te maximetre, autoconsum o es indexat.
            # Si no es compleix cap dels 3 no cal revisar res.
            polissa_id = None
            autoconsum, maximetres, indexada = False, False, False
            autoconsum = fact_xml.te_autoconsum()
            if not autoconsum:  # No cal comprovarles les 3 si la primera ja es compleix
                start_date = datetime.strptime(fact_xml.datos_factura.fecha_desde_factura, '%Y-%m-%d')
                start_date += timedelta(days=1)
                data_inici = start_date.strftime('%Y-%m-%d')
                polissa_id = lect_helper.find_polissa_with_cups_id(
                    cursor, uid, line.cups_id.id, data_inici, fact_xml.datos_factura.fecha_hasta_factura
                )
                context = {'date': fact_xml.datos_factura.fecha_hasta_factura, 'from_f1': True, 'avoid_error': True}
                polissa_vals = polissa_obj.read(cursor, uid, polissa_id, ['mode_facturacio', 'facturacio_potencia'], context=context)
                maximetres = polissa_vals['facturacio_potencia'] == 'max'
                indexada = polissa_vals['mode_facturacio'] == 'index'

            if autoconsum or maximetres or indexada:
                # Si hi ha altres F1 amb error de importacio no hem de mirar res
                cups_text = line.cups_text
                sp = [
                    ('cups_text', '=', cups_text),
                    ('fecha_factura_desde', '<=', fact_xml.datos_factura.fecha_desde_factura),
                    ('import_phase', '!=', '50'),
                    ('state', '=', 'erroni'),
                    ('id', '!=', line.id),
                ]
                altres_f1 = f1_o.search(cursor, uid, sp, limit=1)
                if not altres_f1:
                    # Ara toca mirar forats
                    if not polissa_id:
                        start_date = datetime.strptime(fact_xml.datos_factura.fecha_desde_factura, '%Y-%m-%d')
                        start_date += timedelta(days=1)
                        data_inici = start_date.strftime('%Y-%m-%d')
                        polissa_id = lect_helper.find_polissa_with_cups_id(
                            cursor, uid, line.cups_id.id, data_inici, fact_xml.datos_factura.fecha_hasta_factura
                        )

                    # El camp funcio se suposa que ja fa la feina
                    te_forats = polissa_obj.read(cursor, uid, polissa_id, ['f1_foradat'])['f1_foradat']
                    if te_forats:
                        errors.append({})
        return errors

    def check_f1_foradat_fase_4(self, cursor, uid, line, f1, parameters=None):
        f1_o = self.pool.get('giscedata.facturacio.importacio.linia')
        lect_helper = self.pool.get('giscedata.lectures.switching.helper')
        polissa_obj = self.pool.get('giscedata.polissa')
        errors = []
        for fact_xml in f1.facturas_atr:
            if not fact_xml.datos_factura.fecha_desde_factura:
                continue  # N'hauria de tenir. Sino vol dir que es de conceptes i no hem de fer res
            if fact_xml.datos_factura.tipo_factura != 'N':
                continue

            es_20td = fact_xml.datos_factura.tarifa_atr_fact == '018'
            if es_20td:
                # Si hi ha altres F1 amb error de importacio no hem de mirar res
                cups_text = line.cups_text
                sp = [
                    ('cups_text', '=', cups_text),
                    ('fecha_factura_desde', '<=', fact_xml.datos_factura.fecha_desde_factura),
                    ('import_phase', '!=', '50'),
                    ('state', '=', 'erroni'),
                    ('id', '!=', line.id),
                ]
                altres_f1 = f1_o.search(cursor, uid, sp, limit=1)
                if not altres_f1:
                    # Ara toca mirar forats
                    start_date = datetime.strptime(fact_xml.datos_factura.fecha_desde_factura, '%Y-%m-%d')
                    start_date += timedelta(days=1)
                    data_inici = start_date.strftime('%Y-%m-%d')
                    polissa_id = lect_helper.find_polissa_with_cups_id(
                        cursor, uid, line.cups_id.id, data_inici, fact_xml.datos_factura.fecha_hasta_factura
                    )
                    # El camp funcio se suposa que ja fa la feina
                    te_forats = polissa_obj.read(cursor, uid, polissa_id, ['f1_foradat'])['f1_foradat']
                    if te_forats:
                        errors.append({})
        return errors


GiscedataFacturacioSwitchingValidator()
