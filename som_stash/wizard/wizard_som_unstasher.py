# -*- encoding: utf-8 -*-
from osv import fields, osv
from tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta


class WizardSomUnstasher(osv.osv_memory):
    """Wizard to automate the unstashing action"""
    _name = 'wizard.som.unstasher'

    def _default_count(self, cursor, uid, context=None):
        res = 0
        if context:
            res = len(context.get("active_ids", []))
        return res

    def do_unstash_process(self, cursor, uid, ids, context=None):
        msg = _("Resultat d'execució del wizard de desfer el backup de dades:\n")
        # do not commit
        import pudb; pu.db
        wiz = self.read(
            cursor, uid, ids, [], context=context
        )[0]

        item_ids = context.get("active_ids", [])

        som_stash_obj = self.pool.get("som.stash")
        list_ok, errors = som_stash_obj.do_unstash(
                cursor, uid, item_ids, context=context
        )
        
        msg += _(
            "\nRecuperades {} entrades d'estash.\nLlista d'Ids:\n{}".format(
                len(list_ok),
                ', '.join([str(i) for i in list_ok if i])
            )
        )

        if errors:
            msg += _(
                "\n{} Errors trobats recuperant entrades d'estash.\nLlista d'errors:\n".
                format(
                    len(errors)
                )
            )
            for error in errors:
                msg += _(
                    "\nID {} ERROR {}\n".format(
                    str(error[0]), error[1]
                    )
                )
                
        self.write(
            cursor, uid, ids, {'info': msg}
        )

    _columns = {
        'count': fields.integer(_('Registres seleccionats'), readonly=True),
        'info': fields.text(_('Informació'), readonly=True),
    }

    _defaults = {
        'count': _default_count,
    }


WizardSomUnstasher()
