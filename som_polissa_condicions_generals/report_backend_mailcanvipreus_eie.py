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

    def getImpostos(self, fiscal_position, context=False):
        imp_str = "IVA del 10%" if context and context.get('iva10') else "IVA del 21%"
        imp_value = 21
        if fiscal_position:
            if fiscal_position.id in [33, 47, 56, 52, 61, 38, 21, 19, 87, 89, 94]:
                imp_str = "IGIC del 3%"
                imp_value = 3
            if fiscal_position.id in [34, 48, 53, 57, 53, 62, 39, 25, 88, 90]:
                imp_str = "IGIC del 0%"
                imp_value = 0
        return imp_str, float(imp_value)

    @report_browsify
    def get_data(self, cursor, uid, env, context=None):
        imd_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}

        impostos_str, impostos_value = self.getImpostos(env.polissa_id.fiscal_position_id, context)

        if impostos_str == 'IVA del 10%':
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
