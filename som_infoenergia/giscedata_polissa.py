# -*- coding: utf-8 -*-
from osv import osv, fields
import re

from tools.translate import _

class GiscedataPolissaInfoenergia(osv.osv):
    """
        Pòlissa per afegir els camps relacionats amb infoenergia
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def write(self, cursor, uid, ids, vals, context=None):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        if 'emp_allow_recieve_mail_infoenergia' in vals:
            profile_obj = self.pool.get('empowering.customize.profile')
            profile_id = None
            if vals['emp_allow_recieve_mail_infoenergia']:
                profile_id = profile_obj.search(cursor, uid, [('name','=', 'Default profile')])[0]
            vals['empowering_profile_id'] = profile_id

        if 'emp_allow_send_data' in vals:
            if not vals['emp_allow_send_data']:
                vals['emp_allow_recieve_mail_infoenergia'] = False

        res = super(GiscedataPolissaInfoenergia, self).write(cursor, uid, ids, vals, context)
        return res

    _columns = {
        'emp_allow_send_data': fields.boolean('Permetre compartir dades amb BeeData',
                                  help="Compartir dades a través de l'API amb BeeData"),
        'emp_allow_recieve_mail_infoenergia': fields.boolean('Permetre rebre informes',
                                  help="Indica si es vol rebre informes per email del servei"
                                       "d'infoenergia"),
    }
    _defaults = {
        'emp_allow_send_data': lambda *a: True,
        'emp_allow_recieve_mail_infoenergia': lambda *a: True,
    }

GiscedataPolissaInfoenergia()
