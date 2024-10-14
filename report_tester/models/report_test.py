# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class ReportTest(osv.osv):

    _name = "report.test"
    _order = "priority"

    _columns = {
        "name": fields.char(_("Name"), size=64, required=True),
        "description": fields.text(
            _("Descripció"), help=_(u"Descipció del que es vol testejar amb aquest test")),
        "priority": fields.integer(_("Order"), required=True),
        "active": fields.boolean(
            string=_(u"Actiu"), help=_(u"Indica si el test s'ha d'executar o no")
        ),
        "group_id": fields.many2one("report.test.group", _(u"Grup de tests"), required=True),
    }

    _defaults = {
        "active": lambda *a: True,
    }


ReportTest()
