# -*- coding: utf-8 -*-
from osv import fields, osv
from tools.translate import _


class WizardSomStasher(osv.osv_memory):
    """Wizard to automate the stashing action"""
    _name = 'wizard.som.stasher'

    def do_stash_process(self, cursor, uid, ids, context=None):
        # variables temporals
        # years = 6
        som_stash_obj = self.pool.get("som.stash")
        # som_stash_setting_obj = self.pool.get("som.stash.setting")
        models_to_stash = som_stash_obj._get_selectable_models_list(cursor, uid, context=context)

        msg = _("Resultat d'execució del wizard de backup de dades:\n")
        do_stash = self.read(
            cursor, uid, ids, ['do_stash'], context=context
        )[0]['do_stash']

        # explore models to get the data to be stashed
        if do_stash:
            pass
            # do the stash process
            for model in models_to_stash:
                pass
                # stash_setting_fields = som_stash_setting_obj.search

        self.write(
            cursor, uid, ids, {'info': msg}
        )

    _columns = {
        'info': fields.text('Informació', readonly=True),
        'do_stash': fields.boolean(
            'Modifica',
            help=_('Si la casella esta marcada, es realitzaran canvis als '
                   'regsitres trobats')
        )
    }

    _defaults = {
        "do_stash": lambda *a: False,
    }


WizardSomStasher()
