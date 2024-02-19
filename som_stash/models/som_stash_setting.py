# -*- encoding: utf-8 -*-
from osv import fields, osv
from tools.translate import _
from som_stash import SELECTABLE_MODELS_LIST, SELECTABLE_TYPES_LIST


class SomStashSetting(osv.osv):
    _name = 'som.stash.setting'

    _columns = {
        'allowed_models': fields.text('allowed models'),
        'allowed_types': fields.text('allowed types'),
        'model': fields.many2one('ir.model', 'Model'),
        'field': fields.many2one('ir.model.fields', 'Camp'),
        'default_stashed_value': fields.text(_('Valor per defecte')),
    }

    _defaults = {
        "allowed_models": lambda *a: SELECTABLE_MODELS_LIST[:],
        "allowed_types": lambda *a: SELECTABLE_TYPES_LIST[:],
    }

    _sql_constraints = [
        ('model_field_uniq', 'unique(model,field)',
         'You cannot have one field configured more than once'),
    ]


SomStashSetting()
