# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import som_autoreclama_state_condition
import json
import logging


class SomAutoreclamaState(osv.osv):

    _name = 'som.autoreclama.state'
    _order = 'priority'

    def do_action(self, cursor, uid, state_id, atc_id, context=None):
        logger = logging.getLogger('openerp.som_autoreclama')

        state_data = self.read(cursor, uid, state_id, ['name', 'active', 'generate_atc_parameters'])
        state_actv = state_data['active']
        state_name = state_data['name']
        if not state_actv:
            logger.warning(
                u"Acció canvi d'estat per cas ATC {}, estat {} --> DESACTIVADA".format(
                    atc_id,
                    state_name
                )
            )
            return {'status': False, 'error': 'Disabled'}

        state_action_params = state_data['generate_atc_parameters']
        model = state_action_params.get('model', None)
        method = state_action_params.get('method', None)
        params = state_action_params.get('params', {})
        if not state_action_params or not model or not method:
            logger.info(
                u"Acció canvi d'estat per cas ATC {}, estat {} --> sense acció determinada".format(
                    atc_id,
                    state_name
                )
            )
            return {'status': True, 'created_atc': None}

        try:
            model_obj = self.pool.get(model)
            model_method = getattr(model_obj, method)
            if params:
                new_atc_id = model_method(cursor, uid, params, context)
            else:
                new_atc_id = model_method(cursor, uid, atc_id, context)
        except Exception as e:
            logger.error(
                u"Acció canvi d'estat per cas ATC {}, estat {} --> ERROR {}.{} {} : <{}>".format(
                    atc_id,
                    state_name,
                    model,
                    method,
                    params,
                    e.message
                )
            )
            return {'status': False, 'error': e.message}

        logger.info(
            u"Acció canvi d'estat per cas ATC {}, estat {} --> EXECUTADA {}.{} {}".format(
                atc_id,
                state_name,
                model,
                method,
                params
            )
        )
        return {'status': True, 'created_atc': new_atc_id}

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
