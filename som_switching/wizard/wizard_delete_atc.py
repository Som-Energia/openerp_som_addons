# -*- coding: utf-8 -*-
from tools.translate import _
from osv import osv, fields

class WizardDeleteAtc(osv.osv_memory):
    _name = 'wizard.delete.atc'

    def _get_atc_info(self, cursor, uid, context=None):
        return '\n'.join(str(x) for x in context.get('active_ids',[]))

    def delete_atc(self, cursor, uid, ids, context=None):
        resgroups_obj = self.pool.get('res.groups')
        user_obj = self.pool.get('res.users')

        group_ids = user_obj.read(
            cursor, uid, uid, ['groups_id'], context=context
        )['groups_id']

        group_id = resgroups_obj.search(
            cursor, uid, [('name', '=', 'Som Switching / Delete ATC')]
        )[0]

        if group_id not in group_ids:
            raise osv.except_osv(
                _(u"Error"),
                _(u"No tens permisos per realitzar aquesta acció. Per més informació contacta amb el referent de Reclama.")
            )

        atc_obj = self.pool.get('giscedata.atc')

        atc_cases = context.get('active_ids',[])
        res = atc_obj.delete_atc(cursor, uid, atc_cases, context)

        return {
            'type': 'ir.actions.act_window_close',
        }

    _columns = {
        'info': fields.text("info")
    }

    _defaults = {
        'info': _get_atc_info
    }

WizardDeleteAtc()
