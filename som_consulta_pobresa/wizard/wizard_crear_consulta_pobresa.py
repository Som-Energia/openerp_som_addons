# -*- coding: utf-8 -*-
from osv import osv


class WizardCrearConsultaPobresa(osv.osv_memory):

    _name = "wizard.crear.consulta.pobresa"

    def crear_consulta_pobresa(self, cursor, uid, ids, context=None):

        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        scp_obj = self.pool.get('som.consulta.pobresa')
        active_ids = context.get("active_ids")
        for _id in active_ids:
            scp_obj.create(cursor, uid, {
                'polissa_id': _id
            })

        return {
            "domain": "[('id','in', %s)]" % str(active_ids),
            "name": "Consultes pobresa creades",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "som.consulta.pobresa",
            "type": "ir.actions.act_window",
        }


WizardCrearConsultaPobresa()
