# -*- encoding: utf-8 -*-
from osv import fields, osv
from tools.translate import _
from datetime import datetime

SELECTABLE_MODELS = [
    ("res.partner", _("Fitxa client")),
    ("res.partner.address", _("Adreça fitxa client")),
]

SELECTABLE_MODELS_LIST = [tup[0] for tup in SELECTABLE_MODELS]

SELECTABLE_TYPES_LIST = ['char', 'text']


class SomStash(osv.osv):
    _name = 'som.stash'

    def _get_selectable_models_list(self, cursor, uid, context=None):
        return SELECTABLE_MODELS_LIST

    def get_fields_to_stash(self, cursor, uid, model):
        ir_obj = self.pool.get('ir.model')
        setting_obj = self.pool.get("som.stash.setting")

        model_ids = ir_obj.search(cursor, uid, [('model', '=', model)])
        if len(model_ids) != 1:
            return {}

        stash_setting_ids = setting_obj.search(
            cursor, uid, [('model', '=', model_ids[0])]
        )
        if not stash_setting_ids:
            return {}

        fields = {}
        for setting in setting_obj.browse(cursor, uid, stash_setting_ids):
            fields[setting.field.name] = setting.default_stashed_value

        return fields

    def do_stash_item_field(self, cursor, uid, item_id, field, old_value, default_value, key_ref_origin, context=None):  # noqa: E501
        if not old_value:
            return False

        if old_value == default_value:
            return False

        values = {
            'origin': key_ref_origin,
            'res_field': field,
            'res_id': item_id,
            'value': old_value,
            'date_stashed': datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S'),
        }

        self.create(cursor, uid, values, context=context)
        return True

    def do_stash_item(self, cursor, uid, item_id, model, fields, context=None):
        model_obj = self.pool.get(model)
        data_to_bkp = model_obj.read(cursor, uid, item_id, fields.keys())
        key_ref = "{},{}".format(model, str(item_id))

        dict_write = {}
        for field in fields.keys():
            if self.do_stash_item_field(
                    cursor, uid,
                    item_id, field, data_to_bkp[field], fields[field], key_ref,
                    context=context,
            ):
                dict_write[field] = fields[field]

        if dict_write:
            model_obj.write(cursor, uid, item_id, dict_write, context=context)

    def do_stash(self, cursor, uid, ids, model, context=None):
        setting_fields = self.get_fields_to_stash(cursor, uid, model)
        for item_id in ids:
            self.do_stash_item(cursor, uid, item_id, model, setting_fields, context=context)

    _columns = {
        'origin': fields.reference(_('Origen'), selection=SELECTABLE_MODELS, size=128),
        'res_field': fields.char(_('Camp'), size=64),
        'res_id': fields.integer(_('ID')),
        'value': fields.text(_('Valor')),
        'date_stashed': fields.datetime(_('Data backup')),
    }

    _defaults = {
    }

    _sql_constraints = [
        ('origin_field_date_stashed_uniq', 'unique(origin, res_field, date_stashed)',
         'You cannot have an origin and field more than once at the same time'),
    ]


SomStash()
