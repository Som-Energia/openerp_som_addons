# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import som_autoreclama_state_condition
import json

class SomAutoreclamaState(osv.osv):

    _name = 'som.autoreclama.state'
    _order = 'priority'


    def do_action(self, cursor, uid, state_id, atc_id, context=None):
        state_data = self.read(cursor, uid, state_id, ['name', 'active'])
        state_actv = state_data['active']
        state_name = state_data['name']

        if not state_actv:
            print u"[DESACTIVADA] Acció canvi d'estat per cas ATC {}, estat {}".format(atc_id, state_name)
            return False

        print "Acció canvi d'estat per cas ATC {}, estat {}".format(atc_id, state_name)
        return True


    def _ff_generate_atc_parameters(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}

        res = {}
        for import_vals in self.read(cursor, uid, ids, ['generate_atc_parameters']):
            res[import_vals['id']] = json.dumps(
                import_vals['generate_atc_parameters'], indent=4
            )
        return res

    def _fi_generate_atc_parameters(self, cursor, uid, ids, name, value, arg, context=None):
        if not context:
            context = {}

        try:
            parameters = json.loads(value)
            self.write(cursor, uid, ids, {'generate_atc_parameters': parameters})
        except ValueError as e:
            pass

    def check_correct_json(self, cursor, uid, ids, generate_atc_parameters_text):
        try:
            params = json.loads(generate_atc_parameters_text)
        except ValueError as e:
            return {
                'warning': {
                    'title': _(u'Atenció!'),
                    'message': _('Els parametres entrats no tenen un format '
                                 'correcte de JSON')
                }
            }
        if not isinstance(params, dict):
            return {
                'warning': {
                    'title': _(u'Atenció'),
                    'message': _('Els parametres han de ser un diccionari')
                }
            }
        return {}

    _columns = {
        'name': fields.char(
            _('Name'),
            size=64,
            required=True
        ),
        'priority': fields.integer(
            _('Order'),
            required=True
        ),
        'is_last': fields.boolean(
            string=_(u'Últim'),
            help=_(u"Indica si es l'utim estat")
        ),
        'conditions_ids': fields.one2many(
            'som.autoreclama.state.condition',
            'state_id',
            u"Condicions per canviar d'estat",
        ),
        'workflow_id': fields.many2one(
            'som.autoreclama.state.workflow',
            _(u'Workflow'),
            required=True
        ),
        'active': fields.boolean(
            string=_(u'Actiu'),
            help=_(u"Indica si l'estat està actiu i pot executar la tasca")
        ),
        'generate_atc_parameters': fields.json("Parametres de generació d'ATC"),
        'generate_atc_parameters_text': fields.function(
            _ff_generate_atc_parameters,
            type='text',
            method=True,
            string=_("Parametres de generació d'ATC"),
            fnct_inv=_fi_generate_atc_parameters
        ),
    }

    _defaults = {
        'is_last': lambda *a: False,
        'active': lambda *a: True,
    }

SomAutoreclamaState()
