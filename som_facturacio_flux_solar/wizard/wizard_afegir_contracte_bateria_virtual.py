# -*- coding: utf-8 -*-
from osv import fields, osv


class WizardAfegirContracteBateriaVirtual(osv.osv_memory):
    """Wizard per afegir contractes a un bateria virtual
    """
    _name = "wizard.afegir.contracte.bateria.virtual"
    _inherit = "wizard.afegir.contracte.bateria.virtual"

    def get_auto_bat_name(self, cursor, uid, polissa_id, polissa_name, context=None):
        if context is None:
            context = {}
        return "FS" + str(polissa_name)


WizardAfegirContracteBateriaVirtual()

