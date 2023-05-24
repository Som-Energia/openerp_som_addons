# -*- coding: utf-8 -*-
import time
from osv import fields, osv
from tools.translate import _
from datetime import datetime

class WizardAfegirContracteBateriaVirtual(osv.osv_memory):
    """Wizard per afegir contractes a un bateria virtual
    """
    _name = "wizard.afegir.contracte.bateria.virtual"
    _inherit = 'wizard.afegir.contracte.bateria.virtual'

    def action_assignar_bateria_virtual(self, cursor, uid, ids, context=None):
        # validar origens
        
        # cridar al super



WizardAfegirContracteBateriaVirtual()
