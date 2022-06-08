from giscedata_facturacio.report.utils import get_atr_prices
from datetime import datetime

class power_prices():

    def get_data(self, cursor, uid, object, extra_text, context):
        tariff = 'error'
        polissa = object.polissa_id
        preus = {
            'tariff': '',
            'preu_p1': '',
            'preu_p2': '',
            'preu_p3': '',
            'preu_p4': '',
            'preu_p5': '',
            'preu_p6': '',
        }
        if polissa:
            preus['tariff'] = polissa.tarifa_codi
            ctx = {'date': False}
            data_final = polissa.modcontractual_activa.data_final or ''
            if data_final:
                data_llista_preus = min(datetime.strptime(data_final, '%Y-%m-%d'), datetime.today())
                ctx['date'] = data_llista_preus

            periodes_potencia = sorted(polissa.tarifa.get_periodes('tp', context=ctx).keys())

            for p in periodes_potencia:
                preus['preu_{0}'.format(p)] = get_atr_price(cursor, uid, polissa, p, 'tp', ctx, with_taxes=True)[0]

        return preus