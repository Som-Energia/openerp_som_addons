# -*- coding: utf-8 -*-
from mako.template import Template
from osv import osv


class UiqmakoHelper(osv.osv_memory):
    _name = "som.uiqmako.helper"

    def render_mako_text(self, cursor, uid, id, message, model, recid, context={}):
        context.update({"browse_reference": True})
        object = self.pool.get(model).browse(cursor, uid, recid, context)
        env = context.copy()
        env.update(
            {
                "user": self.pool.get("res.users").browse(cursor, uid, uid, context),
                "db": cursor.dbname,
            }
        )

        templ = Template(message, input_encoding="utf-8")
        extra_render_values = env.get("extra_render_values", {}) or {}
        values = {
            "object": object,
            "peobject": object,
            "env": env,
            "format_exceptions": True,
        }
        values.update(extra_render_values)
        reply = templ.render_unicode(**values)
        return reply


UiqmakoHelper()
