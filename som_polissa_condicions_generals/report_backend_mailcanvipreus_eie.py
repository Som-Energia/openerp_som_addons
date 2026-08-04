# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from som_indexada.utils import calculate_new_indexed_prices


class ReportBackendMailcanvipreusEiE(ReportBackend):
    _source_model = "som.enviament.massiu"
    _name = "report.backend.mailcanvipreus.eie"

    _decimals = {
        ("conany"): 0,
        ("dades_index", "f_antiga"): 3,
        ("dades_index", "f_nova"): 3,
        ("dades_index", "f_antiga_kwh"): 6,
        ("dades_index", "f_nova_kwh"): 6,
        ("dades_index", "ie"): 2,
        ("dades_index", "impacte_import"): 2,
        ("dades_index", "impacte_import_amb_impost"): 2,
        ("dades_index", "import_energia_anual_antiga"): 2,
        ("dades_index", "import_energia_anual_nova"): 2,
        ("dades_index", "import_potencia_anual_antiga"): 2,
        ("dades_index", "import_potencia_anual_nova"): 2,
        ("dades_index", "import_total_anual_antiga"): 2,
        ("dades_index", "import_total_anual_antiga_amb_impost"): 2,
        ("dades_index", "import_total_anual_nova"): 2,
        ("dades_index", "import_total_anual_nova_amb_impost"): 2,
        ("dades_index", "iva"): 2,
        ("dades_index", "pot_contractada"): 2,
        ("dades_index", "preu_mig_anual_antiga"): 2,
        ("dades_index", "preu_mig_anual_nova"): 2,
        ("dades_index", "preu_sense_F"): 2,
    }

    def get_lang(self, cursor, uid, record_id, context=None):
        if context is None:
            context = {}

        env_o = self.pool.get("som.enviament.massiu")
        env_br = env_o.browse(cursor, uid, record_id, context=context)

        return env_br.polissa_id.titular.lang

    def get_data_eie(self, cursor, uid, env, context=None):
        if context is None:
            context = {}

        data = {
            'cups': env.polissa_id.cups.name,
            'titular': env.polissa_id.titular.name,
            'numero': env.polissa_id.name
        }

        return data

    def get_iva_text(self, context=None):
        if 'IGIC' in self.simplified_taxes:
            return 'IGIC del {}%'.format(int(self.simplified_taxes['IGIC'] * 100))
        else:
            return 'IVA del {}%'.format(int(self.simplified_taxes['IVA'] * 100))

    @report_browsify
    def get_data(self, cursor, uid, env, context=None):
        imd_obj = self.pool.get('ir.model.data')
        pol_obj = self.pool.get("giscedata.polissa")
        if context is None:
            context = {}

        self.simplified_taxes = pol_obj.get_simplified_taxes(
            cursor, uid, env.polissa_id.id, context=context)

        if 'IVA' in self.simplified_taxes and self.simplified_taxes['IVA'] < 0.21:
            fp_id = imd_obj.get_object_reference(
                cursor, uid, 'som_polissa_condicions_generals', 'fp_iva_reduit')[1]
            context.update({'force_fiscal_position': fp_id})

        data = {
            "lang": env.polissa_id.titular.lang,
        }

        data['dades_index'] = calculate_new_indexed_prices(
            cursor, uid, env.polissa_id, context=context
        )
        data['contract'] = self.get_data_eie(cursor, uid, env, context=context)

        return data


ReportBackendMailcanvipreusEiE()
