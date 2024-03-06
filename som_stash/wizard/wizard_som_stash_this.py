# -*- encoding: utf-8 -*-
from osv import fields, osv
from tools.translate import _


class WizardSomStashThis(osv.osv_memory):
    """Wizard to automate the stashing action"""
    _name = 'wizard.som.stash.this'

    def do_stash_process(self, cursor, uid, ids, context=None):
        msg = _("Resultat d'execució del wizard de backup de dades:\n\n")

        if not context:
            context = {}

        par_ids = context.get("active_ids", [])
        if not par_ids:
            msg += _("Cap fitxa client per fer backup i anonimització.")
        else:
            stash_obj = self.pool.get("som.stash")
            p, a = stash_obj.do_stash_partner(cursor, uid, par_ids, None, context=context)

            msg += _("{} fitxes client anonimitzades\n".format(len(p)))
            msg += _("Ids: {}\n\n".format(', '.join([str(x) for x in p])))

            msg += _("{} adreçes client anonimitzades\n".format(len(a)))
            msg += _("Ids: {}\n".format(', '.join([str(x) for x in a])))

        self.write(
            cursor, uid, ids, {'info': msg}
        )

    _columns = {
        'info': fields.text('Informació', readonly=True),
    }

    _defaults = {
    }


WizardSomStashThis()
