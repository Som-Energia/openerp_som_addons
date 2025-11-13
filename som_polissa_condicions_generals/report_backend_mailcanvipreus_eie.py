# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from som_indexada.utils import calculate_new_indexed_prices


class ReportBackendMailcanvipreusEiE(ReportBackend):
    _source_model = "som.enviament.massiu"
    _name = "report.backend.mailcanvipreus.eie"

    # def is_eie(self, cursor, uid, env, context=None):
    #     if context is None:
    #         context = {}

    #     pol_llista = env.polissa_id.llista_preu.id

    #     return pol_llista in [150, 153, 154]

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
