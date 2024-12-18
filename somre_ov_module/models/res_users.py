# -*- coding: utf-8 -*-
from osv import osv, fields


class ResUsers(osv.osv):
    _inherit = 'res.users'

    def _fnt_is_staff(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        res = dict.fromkeys(ids, False)
        res_user_obj = self.pool.get('res.users')

        for res_user_id in ids:
            res[res_user_id] = self._is_user_staff(cursor, uid, res_user_obj, res_user_id)

        return res

    def _is_user_staff(self, cursor, uid, res_user_obj, res_user_id):
        res_user = res_user_obj.browse(cursor, uid, res_user_id)
        address_id = res_user.address_id
        if address_id:
            partner = address_id.partner_id
            return True if partner else False
        return False

    def _fnt_is_staff_search(self, cursor, uid, obj, name, args, context=None):
        if not context:
            context = {}
        res = []
        ids = self.search(cursor, uid, [])

        selection_value = args[0][2]
        res_user_obj = self.pool.get('res.users')

        for res_user_id in ids:
            is_staff = self._is_user_staff(cursor, uid, res_user_obj, res_user_id)
            if is_staff == selection_value:
                res.append(res_user_id)

        return [('id', 'in', res)]

    _columns = {
        'is_staff': fields.function(
            _fnt_is_staff,
            fnct_search=_fnt_is_staff_search,
            type='boolean',
            method=True,
            string='És usuària OV staff',
            store=False,
            bold=True,
        )
    }


ResUsers()
