from giscedata_facturacio.report.utils import get_atr_price
from datetime import datetime


class power_prices:
    def get_data(self, cursor, uid, object, extra_text, context):
        polissa = object.polissa_id
        preus = {
            "tariff": "",
            "preu_P1": 0,
            "preu_P2": 0,
            "preu_P3": 0,
            "preu_P4": 0,
            "preu_P5": 0,
            "preu_P6": 0,
        }
        if polissa and polissa.tarifa.codi_ocsum in (
            "020",
            "021",
            "022",
            "023",
            "025",
            "019",
            "024",
        ):
            preus["tariff"] = polissa.tarifa_codi
            ctx = {"date": False}
            ctx["potencia_anual"] = True
            ctx["sense_agrupar"] = True

            data_final = polissa.modcontractual_activa.data_final or ""
            if data_final:
                data_llista_preus = min(datetime.strptime(data_final, "%Y-%m-%d"), datetime.today())
                ctx["date"] = data_llista_preus

            periodes_potencia = sorted(polissa.tarifa.get_periodes("tp", context=ctx).keys())

            for p in periodes_potencia:
                preus["preu_{0}".format(p)] = get_atr_price(
                    cursor, uid, polissa, p, "tp", ctx, with_taxes=False
                )[0]

        return preus
