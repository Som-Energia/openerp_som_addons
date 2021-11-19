# -*- coding: utf-8 -*-
from osv import osv, fields
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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

    def get_consum_anual_consum_lectures(self, cursor, uid, polissa_id, context=None):
        """Calculem el consum anual a partir del consum de les lectures"""

        if isinstance(polissa_id, (tuple, list)):
            polissa_id = polissa_id[0]

        lectures_obj = self.pool.get('giscedata.lectures.lectura')
        limit_date = (datetime.today() - timedelta(122)).strftime('%Y-%m-%d')

        from_date = (datetime.today() - relativedelta(months=14)).strftime('%Y-%m-%d')

        search_params = [
            ('comptador.polissa', '=', polissa_id),
            ('name', '>', from_date),
            ('tipus', '=', 'A'),
        ]
        lect_ids = lectures_obj.search(
            cursor, uid, search_params, context={'active_test': False}
        )

        lect_info = lectures_obj.read(cursor, uid, lect_ids, ['consum', 'name'])
        lect_info.sort(key=lambda x: x['name'])
        if not lect_ids or lect_info[0]['name'] > limit_date:
            return False

        consum = sum([x['consum'] for x in lect_info])
        n_dies = datetime.strptime(lect_info[-1]['name'], '%Y-%m-%d') - datetime.strptime(lect_info[0]['name'], '%Y-%m-%d')
        n_dies = n_dies.days
        if n_dies:
            return consum*365/n_dies

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
