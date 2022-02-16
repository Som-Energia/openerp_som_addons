# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import json

class SomAutoreclamaPendingStateWorkflow(osv.osv):

    _name = 'som.autoreclama.pending.state.workflow'

    WORKFLOW_MODELS = [
        ('r1', 'R1')
    ]
    _columns = {
        'name': fields.char(_('Name'), size=64, required=True),
        'model': fields.selection(WORKFLOW_MODELS, 'Model', required=True),
    }

    _defaults = {

    }

SomAutoreclamaPendingStateWorkflow()




class SomAutoreclamaPendingState(osv.osv):

    _name = 'som.autoreclama.pending.state'
    _order = 'priority'


    def _ff_parameters(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}

        res = {}
        for import_vals in self.read(cursor, uid, ids, ['parameters']):
            res[import_vals['id']] = json.dumps(
                import_vals['parameters'], indent=4
            )
        return res

    def _fi_parameters(self, cursor, uid, ids, name, value, arg, context=None):
        if not context:
            context = {}

        try:
            parameters = json.loads(value)
            self.write(cursor, uid, ids, {'parameters': parameters})
        except ValueError as e:
            pass

    def check_correct_json(self, cursor, uid, ids, parameters_text):
        try:
            parameters = json.loads(parameters_text)
        except ValueError as e:
            return {
                'warning': {
                    'title': _(u'Atenció!'),
                    'message': _('Els parametres entrats no tenen un format '
                                 'correcte de JSON')
                }
            }
        if not isinstance(parameters, dict):
            return {
                'warning': {
                    'title': _(u'Atenció'),
                    'message': _('Els parametres han de ser un diccionari')
                }
            }
        return {}

    _columns = {
        'name': fields.char(_('Name'), size=64, required=True),
        'priority': fields.integer('Order', required=True),
        'is_last': fields.boolean(
            string=_(u'Is last'),
            help=_(u'Indicates if the pending state is an ending state')
        ),
        # 'pending_days_ids': fields.one2many(
        #     'som.autoreclama.pending.state.days',
        #     'pending_state_id',
        #     u'Days in state',
        # ),
        'workflow_id': fields.many2one(
            'som.autoreclama.pending.state.workflow', u'Workfow',
            required=True
        ),
        'active': fields.boolean(
            string=u'Active',
            help=u'Indicates if the pending state is active and can be searched'
        ),
        'parameters': fields.json('Parametres'),
        'parameters_text': fields.function(
            _ff_parameters, type='text', method=True, string='Parametres',
            fnct_inv=_fi_parameters
        ),
        'subtype_id': fields.many2one('giscedata.subtipus.reclamacio',
            u"Subtype", required=True),
    }

    _defaults = {
        'is_last': lambda *a: False,
        'active': lambda *a: True,
    }

SomAutoreclamaPendingState()

class SomAutoreclamaPendingStateDays(osv.osv):

    _name = 'som.autoreclama.pending.state.days'
    _rec_name = 'subtype_id'

    _columns = {
        'subtype_id': fields.many2one("giscedata.subtipus.reclamacio",
            u"Subtype", required=True),
        'days': fields.integer(_('Days'), required=True),
        'pending_state_id': fields.many2one(
            'som.autoreclama.pending.state', u'Pending State',
            required=True
        ),
    }


    _defaults = {}

SomAutoreclamaPendingStateDays()


