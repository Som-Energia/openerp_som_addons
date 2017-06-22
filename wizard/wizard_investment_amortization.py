# -*- coding: utf-8 -*-
from __future__ import division
from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta
from calendar import isleap
import netsvc


class WizardInvestmentAmortization(osv.osv_memory):
    """Assistent per amortitzar la inversió.
    """
    _name = 'wizard.generationkwh.investment.amortization'
    _columns = {
        'date_end': fields.date(
            'Data final',
            required=True
        ),
        'err': fields.text(
            'Missatges d\'error',
            readonly=True,
        ),
        'state': fields.char(
            'Estat',
            50
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
    }



WizardInvestmentAmortization()
