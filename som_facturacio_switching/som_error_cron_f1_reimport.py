# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class SomErrorCronF1Reimport(osv.osv):
    _name = "som.error.cron.f1.reimport"

    def _get_fase(self, cursor, uid, ids, name, args, context=None):
        if context is None:
            context = {}
        error_obj = self.pool.get("giscedata.facturacio.switching.error.template")

        res = dict.fromkeys(ids, 0.0)
        for id_registre in ids:
            id_error = self.read(cursor, uid, id_registre, ["error_code"])["error_code"][0]
            fase = error_obj.read(cursor, uid, id_error, ["phase"])["phase"]
            res[id_registre] = fase
        return res

    def _get_code(self, cursor, uid, ids, name, args, context=None):
        if context is None:
            context = {}
        error_obj = self.pool.get("giscedata.facturacio.switching.error.template")

        res = dict.fromkeys(ids, "")
        for id_registre in ids:
            id_error = self.read(cursor, uid, id_registre, ["error_code"])["error_code"][0]
            data = error_obj.read(cursor, uid, id_error, ["code", "phase"])
            code = "{}{}".format(data["phase"], data["code"])
            res[id_registre] = code
        return res

    _columns = {
        "error_code": fields.many2one(
            "giscedata.facturacio.switching.error.template", "Codis d'error de F1"
        ),
        "text": fields.text(
            _(u"Text contingut al F1 erroni"),
            help=_("Text que ha de contenir l'error del F1 que es vol importar"),
        ),
        "active": fields.boolean(
            string=_(u"Actiu"),
            help=_(u"Indica si l'error es reimportarà al cron o no"),
            required=True,
        ),
        "fase": fields.function(_get_fase, string="Fase", type="char", method=True),
        "code": fields.function(_get_code, string="Fase", type="char", method=True),
    }


SomErrorCronF1Reimport()
