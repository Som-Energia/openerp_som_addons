# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class ReportTestGroup(osv.osv):

    _name = "report.test.group"
    _order = "priority"

    def execute_tests(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        rt_obj = self.pool.get("report.test")

        result = ""
        tgs = self.read(cursor, uid, ids, ['active', 'test_ids', 'priority', 'name'])
        for tg in sorted(tgs, key=lambda e: e['priority']):
            if not tg["active"]:
                result += _("Grup de test '{}' no està actiu!!\n\n".format[tg['name']])
            else:
                result += _("Executant tests per grup '{}':\n".format(tg['name']))
                result += rt_obj.execute_test(cursor, uid, tg['test_ids'], context)
                result += "\n"
        return result

    def accept_tests(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        rt_obj = self.pool.get("report.test")

        result = ""
        tgs = self.read(cursor, uid, ids, ['active', 'test_ids', 'priority', 'name'])
        for tg in sorted(tgs, key=lambda e: e['priority']):
            if not tg["active"]:
                result += _("Grup de test '{}' no està actiu!!\n\n".format[tg['name']])
            else:
                result += _("Acceptant tests per grup '{}':\n".format(tg['name']))
                result += rt_obj.accept_test(cursor, uid, tg['test_ids'], context)
                result += "\n"
        return result

    _columns = {
        "name": fields.char(
            _("Nom"),
            size=64,
            required=True
        ),
        "description": fields.text(
            _("Descripció"),
            help=_(u"Descripció del que es vol testejar amb aquest grup de tests")
        ),
        "priority": fields.integer(
            _("Order"),
            required=True
        ),
        "active": fields.boolean(
            string=_(u"Actiu"),
            help=_(u"Indica si el grup de tests s'ha d'executar o no")
        ),
        "test_ids": fields.one2many(
            "report.test",
            "group_id",
            _(u"Tests"),
        ),
        "result": fields.text(
            _("Resultats"),
            help=_(u"Resultat de l'execució dels tests"),
            readonly=True
        ),
    }

    _defaults = {
        "active": lambda *a: True,
        "result": lambda *a: "",
    }


ReportTestGroup()
