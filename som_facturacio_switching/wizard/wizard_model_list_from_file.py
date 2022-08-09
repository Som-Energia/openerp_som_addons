# -*- coding: utf-8 -*-
from tools.translate import _
from osv import osv


class WizardModelListFromFile(osv.osv_memory):
    """Wizard"""
    _name = 'wizard.model.list.from.file'
    _inherit = 'wizard.model.list.from.file'


WizardModelListFromFile()