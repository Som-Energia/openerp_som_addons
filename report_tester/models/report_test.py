# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


EXECUTION_STATES = [
    ("pending", _(u"Pendent")),
    ("doing", _(u"Executant-se")),
    ("equals", _(u"Iguals")),
    ("differents", _(u"Amb diferències")),
    ("error", _(u"Error en generar")),
    ("no_expected", _(u"Sense doc. original")),
]


class ReportTest(osv.osv):

    _name = "report.test"
    _order = "priority"

    _columns = {
        "name": fields.char(_("Name"), size=64, required=True),
        "description": fields.text(
            _("Descripció"), help=_(u"Descripció del que es vol testejar amb aquest test")),
        "priority": fields.integer(_("Order"), required=True),
        "active": fields.boolean(
            string=_(u"Actiu"), help=_(u"Indica si el test s'ha d'executar o no")
        ),
        "group_id": fields.many2one("report.test.group", _(u"Grup de tests"), required=True),
        "result": fields.selection(
            EXECUTION_STATES, _(u"Resultat"),
            help=_("Resultat de la darrera execució"),
            readonly=True
        ),
    }

    _defaults = {
        "active": lambda *a: True,
    }


ReportTest()
