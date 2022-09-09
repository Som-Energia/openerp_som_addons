# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import json

class CallInfoCallCategory(osv.osv):

    _name = 'call.info.call.category'


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
            _(u'Nom'),
            size=240,
            help=_(u"Nom de la categoria")
        ),
        'code': fields.char(
            _('Codi'),
            size=8,
            help=_('Codi de la categoria')
        ),
        'active': fields.boolean('Actiu'),
        'subtipus_reclamacio_id': fields.many2one(
            'giscedata.subtipus.reclamacio',
            _('Tipus Reclamació'),
            help=_('Subtipus de la reclamació associada')
        ),
        'generate_atc_parameters': fields.json("Parametres de generació d'ATC"),
        'generate_atc_parameters_text': fields.function(
            _ff_generate_atc_parameters,
            type='text',
            method=True,
            string=_("Parametres de generació d'ATC"),
            fnct_inv=_fi_generate_atc_parameters
        )
    }

    _defaults = {
        'active': lambda *a: True,
        'generate_atc_parameters_text': lambda *a: '{}',
    }


CallInfoCallCategory()