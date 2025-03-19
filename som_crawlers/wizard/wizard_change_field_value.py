# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardChangeFieldValue(osv.osv_memory):

    _name = "wizard.change.field.value"

    def _default_field_to_change_label(self, cursor, uid, context=None):
        field_to_change_label = False
        if context:
            field_to_change_label = context.get("field_label", False)
        return field_to_change_label

    def change_value(self, cursor, uid, ids, context=None):

        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get("active_ids")
        field_name = context.get("field_name")
        field_label = context.get("field_label")
        is_numeric = context.get("is_numeric")

        conf_obj = self.pool.get("som.crawlers.config")
        wizard = self.browse(cursor, uid, ids[0])
        for id in active_ids:
            conf_obj.change_field_value(
                cursor,
                uid,
                id,
                field_name,
                field_label,
                wizard.new_value_str,
                is_numeric,
                context=context,
            )

        return {"type": "ir.actions.act_window_close"}

    _columns = {
        "new_value_str": fields.char(
            "Nou valor",
            size=300,
            required=True,
        ),
        "field_to_change_label": fields.char(
            "Camp a modificar",
            size=64,
            required=True,
            readonly=True,
        ),
    }

    _defaults = {
        "field_to_change_label": _default_field_to_change_label,
    }


WizardChangeFieldValue()
