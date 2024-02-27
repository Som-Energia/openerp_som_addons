# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


# Class Result that describes the module and result fields
class SomCrawlersResult(osv.osv):
    # Module name
    _name = "som.crawlers.result"
    _order = "data_i_hora_execucio desc"

    def _get_last_result(self, cursor, uid, task_ids, field_name, arg, context=None):
        res = {}
        for task_id in task_ids:
            resultat_text = self.read(cursor, uid, task_id, ["resultat_text"])["resultat_text"]
            if not resultat_text:
                res[task_id] = ""
                continue
            res[task_id] = (
                resultat_text.lstrip()[:50] + "..." if len(resultat_text) > 50 else resultat_text
            )
        return res

    _STORE_WHEN_RESULT_MODIFIED = {
        "som.crawlers.result": (lambda self, cr, uid, ids, c={}: ids, ["resultat_text"], 10)
    }

    # Column fields
    _columns = {
        "name": fields.char(
            _(u"Funció"),
            size=64,
            required=False,
        ),
        "task_id": fields.many2one(
            "som.crawlers.task",
            _("Tasca"),
            help=_("Nom de la tasca"),
            select=True,
        ),
        "data_i_hora_execucio": fields.datetime(
            _(u"Data i hora de l'execució"),
        ),
        "resultat_text": fields.text(
            _(u"Resultat"),
            help=_("Resultat de l'execució"),
        ),
        "zip_name": fields.many2one(
            "ir.attachment",
            _(u"Fitxer adjunt"),
        ),
        "resultat_bool": fields.boolean(
            _(u"Resultat"),
        ),
        "resultat_curt": fields.function(
            _get_last_result,
            string="Resultat",
            type="char",
            size=55,
            method=True,
            store=_STORE_WHEN_RESULT_MODIFIED,
        ),
    }
    _defaults = {
        "resultat_bool": lambda *a: False,
    }


SomCrawlersResult()
