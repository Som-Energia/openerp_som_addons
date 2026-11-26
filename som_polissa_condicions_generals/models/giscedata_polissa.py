# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv
from som_indexada.taxes import get_simplified_taxes


class GiscedataPolissa(osv.osv):
    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def action_imprimir_contract_summary_pdf(self, cursor, uid, ids, context=None):
        return {
            'type': 'ir.actions.report.xml',
            'model': 'giscedata.polissa',
            'report_name': 'giscedata.polissa.contract.summary',
            'groups_id': [(6, 0, [])],
            'multi': '0',
            'auto': '0',
            'header': '0',
            'report_rml': 'False',
            'datas': {
                'ids': ids,
                'form': {},
            },
            'context': context,
        }

    def action_imprimir_contract_summary_full_pdf(self, cursor, uid, ids, context=None):
        return {
            'type': 'ir.actions.report.xml',
            'model': 'giscedata.polissa',
            'report_name': 'giscedata.polissa.contract.summary.full',
            'groups_id': [(6, 0, [])],
            'multi': '0',
            'auto': '0',
            'header': '0',
            'report_rml': 'False',
            'datas': {
                'ids': ids,
                'form': {},
            },
            'context': context,
        }

    def get_simplified_taxes(self, cursor, uid, polissa_id, context=None):
        return get_simplified_taxes(cursor, uid, self, polissa_id, context=context)


GiscedataPolissa()
