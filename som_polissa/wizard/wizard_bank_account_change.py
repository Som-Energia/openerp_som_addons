# -*- coding: utf-8 -*-
from osv import osv


class WizardBankAccountChange(osv.osv_memory):

    _inherit = 'wizard.bank.account.change'

    _defaults = {
        'print_mandate': False,
        'update_fact_no_pagades': True,
    }


WizardBankAccountChange()
