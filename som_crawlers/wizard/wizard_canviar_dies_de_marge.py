# -*- coding: utf-8 -*-
from osv import osv, fields

# @author Ikram Ahdadouche El Idrissi
# @author Dalila Jbilou Kouhous
# Describes the module and contains the function that changes the password


class WizardCanviarDiesDeMarge(osv.osv_memory):

    # Module name
    _name = "wizard.canviar.dies.de.marge"

    # Wizard function that changes the days of margin of a configuration which id is activated
    # @param self The object pointer
    # @param cursor The database pointer
    # @param uid The current user
    # @param ids List of selected configuration
    # @param context None certain data to pass
    # @return ir.actions.act_window_close that closes the wizard window

    def canviar_dies(self, cursor, uid, ids, context=None):

        if not context:
            return False

        # Control ids
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        wiz = self.browse(cursor, uid, ids[0], context=context)
        days_of_margin = wiz.days_of_margin

        active_ids = context.get("active_ids")
        # Load the module
        classconf = self.pool.get("som.crawlers.config")
        for id in active_ids:
            classconf.canviar_dies_de_marge(cursor, uid, id, int(days_of_margin), context=context)

        return {"type": "ir.actions.act_window_close"}

    # Column definition : dies de marge nous, the user puts the margin days
    _columns = {
        "days_of_margin": fields.char(
            "Dies de marge",
            size=10,
            required=True,
            help="Introdueix un nombre >= 0 de dies de marge",
        )
    }


WizardCanviarDiesDeMarge()
