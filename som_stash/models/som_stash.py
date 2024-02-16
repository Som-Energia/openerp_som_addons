# -*- encoding: utf-8 -*-
from osv import fields,osv
from tools.translate import _
import json


class SomStash(osv.osv):
    _name = 'som.stash'

    def _links_get(self, cr, uid, context={}):
        obj = self.pool.get('res.request.link')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['object', 'name'], context)
        return list(set([(r['object'], r['name']) for r in res]))


    def _ff_data_text(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}

        res = {}
        for import_vals in self.read(cursor, uid, ids, ["data"]):
            res[import_vals["id"]] = json.dumps(import_vals["data"], indent=4)
        return res

    def _fi_data_text(self, cursor, uid, ids, name, value, arg, context=None):
        if not context:
            context = {}

        try:
            parameters = json.loads(value)
            self.write(cursor, uid, ids, {"data": parameters})
        except ValueError:
            pass

    def check_correct_json(self, cursor, uid, ids, data):
        try:
            params = json.loads(data)
        except ValueError:
            return {
                "warning": {
                    "title": _(u"Atenció!"),
                    "message": _("Els parametres entrats no tenen un format " "correcte de JSON"),
                }
            }
        if not isinstance(params, dict):
            return {
                "warning": {
                    "title": _(u"Atenció"),
                    "message": _("Els parametres han de ser un diccionari"),
                }
            }
        return {}

    _columns = {
        'origin' : fields.reference('Origen', selection=_links_get, size=128),
        'data': fields.json('Dades'),
        'data_text': fields.function(
            _ff_data_text,
            type="text",
            method=True,
            string=_("Dades"),
            fnct_inv=_fi_data_text,
        ),
    }
    
    _defaults = {
    }
    
    _sql_constraints = [
        ('module_origin_uniq', 'unique(origin)', 'You cannot an origin more than once'),
    ]


SomStash()