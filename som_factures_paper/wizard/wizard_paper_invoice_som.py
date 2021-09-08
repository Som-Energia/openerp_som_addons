# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
import tempfile
from datetime import date, datetime
from yamlns import namespace as ns

STATES = [
    ('init', 'Estat Inicial'),
    ('finished', 'Estat Final')
]

class WizardPaperInvoiceSom(osv.osv_memory):
    _name = 'wizard.paper.invoice.som'

    _columns = {
        #Header
        'state': fields.selection(STATES, _(u'Estat del wizard de imprimir report')),
    }

    _defaults = {
        'state': 'init'
    }

WizardPaperInvoiceSom()