# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class SomAutoreclamaStateWorkflow(osv.osv):

    _name = 'som.autoreclama.state.workflow'

    WORKFLOW_MODELS = [
        ('ATC', 'Cas ATC'),
        ('F1', 'F1'),
    ]
    _columns = {
        'name': fields.char(_('Name'), size=64, required=True),
        'model': fields.selection(WORKFLOW_MODELS, 'Model', required=True),
    }

    _defaults = {

    }


SomAutoreclamaStateWorkflow()
