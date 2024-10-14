# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class ReportTestGroup(osv.osv):

    _name = "report.test.group"
    _order = "priority"

    _columns = {
        "name": fields.char(_("Name"), size=64, required=True),
        "description": fields.text(
            _("Descripció"),
            help=_(u"Descripció del que es vol testejar amb aquest grup de tests")
        ),
        "priority": fields.integer(_("Order"), required=True),
        "active": fields.boolean(
            string=_(u"Actiu"), help=_(u"Indica si el grup de tests s'ha d'executar o no")
        ),
        "test_ids": fields.one2many(
            "report.test",
            "group_id",
            _(u"Tests que formen part del grup de tests"),
        ),
    }

    _defaults = {
        "active": lambda *a: True,
    }


ReportTestGroup()
