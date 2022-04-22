# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from tools import config


class WizardSomAutoreclamaSetManualState(osv.osv_memory):
    _name = 'wizard.som.autoreclama.set.manual.state'

    def do_something(self, cursor, uid, ids, context=None):
        pass


    _columns = {
        'state': fields.selection([('init', 'Init'), ('end', 'End')], 'State'),
        'info': fields.text('Informació', readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: '',
    }

WizardSomAutoreclamaSetManualState()