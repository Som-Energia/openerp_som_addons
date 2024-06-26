# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from giscedata_facturacio.report.utils import get_atr_price

import logging

logger = logging.getLogger("openerp.{}".format(__name__))


class SomPolissaKChange(osv.osv):
    _name = "som.polissa.k.change"
    _description = _("Canvi de K de pòlissa")

    indexada_consum_tipus = {
        "2.0TD": {
            "factor_eie_preu_antic": 133.781131630073,
            "factor_eie_preu_nou": 139.600101568505,
        },
        "3.0TD": {
            "factor_eie_preu_antic": 120.017809474036,
            "factor_eie_preu_nou": 125.837481976305,
        },
        "6.1TD": {
            "factor_eie_preu_antic": 106.055050891024,
            "factor_eie_preu_nou": 111.316018940409,
        },
        "3.0TDVE": {
            "factor_eie_preu_antic": 0,
            "factor_eie_preu_nou": 0,
        },
    }

    def get_fs(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}
        som_polissa_k_change_obj = self.pool.get("som.polissa.k.change")

        search_params = [
            ('partner_id', '=', context['partner_id'])
        ]

        k_change_id = som_polissa_k_change_obj.search(
            cursor, uid, search_params, context=context
        )

        if k_change_id:
            res = som_polissa_k_change_obj.read(
                cursor, uid, k_change_id[0], ['k_old', 'k_new'], context=context
            )

        return res

    def get_preus(self, cursor, uid, pol, with_taxes=False, context=None):
        if context is None:
            context = {}
        context["potencia_anual"] = True

        result = {}
        periods = {
            "tp": sorted(pol.tarifa.get_periodes("tp", context=context).keys()),
            "te": sorted(pol.tarifa.get_periodes("te", context=context).keys()),
            # 'ac': [sorted(pol.tarifa.get_periodes('te', context=context).keys())[0]], # not working for non auto pol  # noqa: E501
        }
        for terme, values in periods.items():
            result[terme] = {}
            for periode in values:
                preu_periode = get_atr_price(
                    cursor, uid, pol, periode, terme, context=context, with_taxes=with_taxes
                )[0]
                result[terme][periode] = preu_periode
        return result

    def calculate_new_eie_indexed_prices(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        f_antiga = self.get_fs(cursor, uid, pol, context=context)['k_old']
        f_nova = self.get_fs(cursor, uid, pol, context=context)['k_new']

        tarifa_acces = pol.tarifa.name
        factor_eie_preu_antic = self.indexada_consum_tipus[tarifa_acces]["factor_eie_preu_antic"]
        factor_eie_preu_nou = self.indexada_consum_tipus[tarifa_acces]["factor_eie_preu_nou"]

        preu_mitja_antic = (1.015 * f_antiga + factor_eie_preu_antic) / 1000
        preu_mitja_nou = (1.015 * f_nova + factor_eie_preu_nou) / 1000

        conany = pol.cups.conany_kwh if pol.cups.conany_kwh > 0 else 1
        potencia = pol.potencia
        preu_potencia = sum(self.get_preus(
            cursor, uid, pol, with_taxes=True, context=context
        )['tp'].values())

        # cost_potencia = preu_potencia * potencia

        import_total_anual_antiga = (preu_mitja_antic * conany)
        import_total_anual_nova = (preu_mitja_nou * conany)
        impacte_import = import_total_anual_nova - import_total_anual_antiga

        import_total_anual_antiga_amb_impost = import_total_anual_antiga * 1.015 * 1.21
        import_total_anual_nova_amb_impost = import_total_anual_nova * 1.015 * 1.21
        impacte_import_amb_impost = (
            import_total_anual_nova_amb_impost - import_total_anual_antiga_amb_impost
        )
        impacte_perc = impacte_import_amb_impost / import_total_anual_antiga_amb_impost

        consum_eie = {
            "conany": conany,
            "pot_contractada": potencia,
            "preu_pot_contractada": preu_potencia,
            "factor_eie_preu_antic": factor_eie_preu_antic,
            "factor_eie_preu_nou": factor_eie_preu_nou,
            "f_antiga": f_antiga,
            "f_nova": f_nova,
            "preu_mig_anual_antiga": preu_mitja_antic,
            "preu_mig_anual_nova": preu_mitja_nou,
            "import_total_anual_antiga": import_total_anual_antiga,
            "import_total_anual_nova": import_total_anual_nova,
            "impacte_import": impacte_import,
            "impacte_perc": impacte_perc * 100,
            "iva": 21,
            "ie": 5.11,
            "import_total_anual_antiga_amb_impost": import_total_anual_antiga_amb_impost,
            "import_total_anual_nova_amb_impost": import_total_anual_nova_amb_impost,
            "impacte_import_amb_impost": impacte_import_amb_impost,
        }

        return consum_eie

    def calculate_multipunt_values(self, cursor, uid, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')

        search_params = [('partner_id', '!=', False)]

        k_change_ids = self.search(cursor, uid, search_params, context=context)

        for k_change in k_change_ids:
            partner_id = self.read(
                cursor, uid, k_change, ['partner_id'], context=context
            )['partner_id'][0]

            import_total_anual_nova_amb_impost = 0
            import_total_anual_antiga_amb_impost = 0
            pol_ids = pol_obj.search(cursor, uid, [
                ('titular', '=', partner_id),
                ('state', '=', 'activa'),
            ])
            for pol in pol_ids:
                context['partner_id'] = partner_id
                pol_browse = pol_obj.browse(cursor, uid, pol, context=context)
                data = self.calculate_new_eie_indexed_prices(
                    cursor, uid, pol_browse, context=context
                )

                import_total_anual_nova_amb_impost += data['import_total_anual_nova_amb_impost']
                import_total_anual_antiga_amb_impost += data['import_total_anual_antiga_amb_impost']

            write_vals = {
                'import_total_anual_nova_amb_impost': import_total_anual_nova_amb_impost,
                'import_total_anual_antiga_amb_impost': import_total_anual_antiga_amb_impost
            }
            self.write(cursor, uid, [k_change], write_vals, context=context)

    _columns = {
        "polissa_id": fields.many2one("giscedata.polissa", "Pòlissa"),
        "k_old": fields.float("K Antiga"),
        "k_new": fields.float("K Nova"),
        "partner_id": fields.many2one("res.partner", "Partner"),
        "import_total_anual_nova_amb_impost": fields.float("Estimat Nova"),
        "import_total_anual_antiga_amb_impost": fields.float("Estimat Antiga"),
    }

    _sql_constraints = [(
        "polissa_id_id_uniq",
        "unique(polissa_id)",
        "La pòlissa ha de ser única"
    )]


SomPolissaKChange()
