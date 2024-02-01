# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


DAYS_TO_CHECK_VARIABLE_NAME = "som_error_cron_f1_reimport_days_to_check"


class WizardChangeCronReimportDays(osv.osv_memory):

    _name = "wizard.change.cron.reimport.days"

    def change_days(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, ids[0])
        confvar_obj = self.pool.get("res.config")
        conf_ids = confvar_obj.search(cursor, uid, [("name", "=", DAYS_TO_CHECK_VARIABLE_NAME)])
        if len(conf_ids) == 1:
            confvar_obj.write(cursor, uid, conf_ids[0], {"value": str(wiz.days)})
        return {}

    def _get_default_days(self, cursor, uid, context=None):
        confvar_obj = self.pool.get("res.config")
        res = int(confvar_obj.get(cursor, uid, DAYS_TO_CHECK_VARIABLE_NAME, 30))
        return res

    _columns = {
        "days": fields.integer(
            "Dies a reimportar",
            help=_(
                u"Canvia el numero de dies a cercar cap enrere del cron de reimportació de F1's a partir d'avuí"
            ),
        ),
    }

    _defaults = {
        "days": _get_default_days,
    }


WizardChangeCronReimportDays()
