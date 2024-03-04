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

    def do_stash_item_field(self, cursor, uid, item_id, field, old_value, default_value, model, date_expiry, origin_partner_id, context=None):  # noqa: E501
        if not old_value:
            return False

        if old_value == default_value:
            return False

        values = {
            'res_field': field,
            'res_id': item_id,
            'res_model': model,
            'value': old_value,
            'date_stashed': datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S'),
            'date_expiry': date_expiry,
            'origin_partner_id': origin_partner_id,
        }

        self.create(cursor, uid, values, context=context)
        return True

    def do_stash_item(self, cursor, uid, item_id, item_data, model, fields, context=None):
        model_obj = self.pool.get(model)
        data_to_bkp = model_obj.read(cursor, uid, item_id, fields.keys())

        dict_write = {}
        for field in fields.keys():
            if self.do_stash_item_field(
                    cursor, uid,
                    item_id, field, data_to_bkp[field], fields[field], model,
                    item_data['date_expiry'],
                    item_data['partner_id'],
                    context=context,
            ):
                dict_write[field] = fields[field]

        if dict_write:
            model_obj.write(cursor, uid, item_id, dict_write, context=context)
            return True
        return False

    def do_stash(self, cursor, uid, items, model, context=None):
        modified = []
        setting_fields = self.get_fields_to_stash(cursor, uid, model)
        for item_id, item_data in items.items():
            if self.do_stash_item(
                cursor, uid, item_id, item_data, model, setting_fields, context=context
            ):
                modified.append(item_id)
        return modified

    def do_unstash_item(self, cursor, uid, item_id, context=None):
        try:
            stash = self.browse(cursor, uid, item_id, context=context)
            model_obj = self.pool.get(stash.res_model)
            values = {
                stash.res_field: stash.value,
            }
            model_obj.write(cursor, uid, stash.res_id, values, context=context)
        except Exception as e:
            return False, str(e)
        return True, item_id

    def do_unstash(self, cursor, uid, ids, context=None):
        res = []
        errors = []
        for item_id in sorted(ids, reverse=True):
            ok, value = self.do_unstash_item(cursor, uid, item_id, context=context)
            if ok:
                res.append(value)
            else:
                errors.append((item_id, value))

        return res, errors

    _columns = {
        'res_field': fields.char(_('Camp'), size=64),
        'res_id': fields.integer(_('ID')),
        'res_model': fields.char(_('Model'), size=128),
        'value': fields.text(_('Valor')),
        'date_stashed': fields.datetime(_('Data backup')),
        'date_expiry': fields.date(_('Última data de caducitat')),
        'origin_partner_id': fields.many2one("res.partner", _('Fitxa clent'), required=True),
    }

    _defaults = {
    }

    _sql_constraints = [
        ('model_field_res_id_date_stashed_uniq',
         'unique(res_model, res_field, res_id, date_stashed)',
         'You cannot have an model and field more than once at the same time'),
    ]


SomStash()
