# -*- encoding: utf-8 -*-
from osv import fields, osv
from tools.translate import _
from som_stash import SELECTABLE_MODELS_LIST, SELECTABLE_TYPES_LIST


class SomStashSetting(osv.osv):
    _name = 'som.stash.setting'

    def _ff_get_allowed(self, cursor, uid, ids, name, args, context=None):
        res = {}
        for val in self.browse(cursor, uid, ids, context=context):
            res[val.id] = {
                'models_domain': str(SELECTABLE_MODELS_LIST),
                'field_types_domain': str(SELECTABLE_TYPES_LIST),
            }
        return res

    _columns = {
        'models_domain': fields.function(
            _ff_get_allowed, type="text", method=True, string="Allowed models", multi=True
        ),
        'field_types_domain': fields.function(
            _ff_get_allowed, type="text", method=True, string="Allowed types", multi=True
        ),
        'model': fields.many2one('ir.model', 'Model'),
        'field': fields.many2one('ir.model.fields', 'Camp'),
        'default_stashed_value': fields.text(_('Valor per defecte')),
    }

    _defaults = {
        "models_domain": lambda *a: str(SELECTABLE_MODELS_LIST),
        "field_types_domain": lambda *a: str(SELECTABLE_TYPES_LIST),
    }

    _sql_constraints = [
        ('model_field_uniq', 'unique(model,field)',
         'You cannot have one field configured more than once'),
    ]


SomStashSetting()
