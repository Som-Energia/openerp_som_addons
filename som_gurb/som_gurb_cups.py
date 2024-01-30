# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import logging
from datetime import datetime

logger = logging.getLogger('openerp.{}'.format(__name__))


class SomGurbCups(osv.osv):
    _name = "som.gurb.cups"
    _description = _('CUPS en grup de generació urbana')

    # TODO: pensar
    def _ff_is_model_active(self, cursor, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        res = dict.fromkeys(ids, False)
        for cups_gurb_id in ids:
            end_date = self.read(cursor, uid, cups_gurb_id, ['end_date'])['end_date']
            if end_date:
                end_date_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                today_time = datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
                if today_time > end_date_datetime:
                    res[cups_gurb_id] = False
                else:
                    res[cups_gurb_id] = True
            else:
                res[cups_gurb_id] = True
        return res

    _columns = {
        'active': fields.boolean('Actiu'),
        'start_date': fields.date(u"Data entrada GURB", required=True),
        'end_date': fields.date(u"Data sortida GURB",),
        'gurb_id': fields.many2one("som.gurb", "GURB", required=True),
        'cups_id': fields.many2one('giscedata.cups.ps', 'CUPS'),
    }

    _defaults = {
        'active': lambda *a: True,
    }


SomGurbCups()
