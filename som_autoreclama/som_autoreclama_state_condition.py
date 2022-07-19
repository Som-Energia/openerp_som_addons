# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import som_autoreclama_state


class SomAutoreclamaStateCondition(osv.osv):

    _name = 'som.autoreclama.state.condition'
    _rec_name = 'subtype_id'
    _order = 'priority'

    def fit_atc_condition(self, cursor, uid, id, data, context=None):
        cond_data = self.read(cursor, uid, id, ['subtype_id', 'days'], context=context)
        return data['subtipus_id'] == cond_data['subtype_id'][0] and data['distri_days'] >= cond_data['days'] and data['agent_actual']=='10' and data['state']=='pending'

    _columns = {
        'priority': fields.integer(
            _('Order'),
            required=True
        ),
        'active': fields.boolean(
            string=_(u'Activa'),
            help=_(u"Indica si la condició esta activa")
        ),
        'subtype_id': fields.many2one(
            "giscedata.subtipus.reclamacio",
            _(u"Subtipus"),
            required=True,
            help=_(u'Subtipus de la reclamació associada al cas ATC')
        ),
        'days': fields.integer(
            _(u"Dies d'espera"),
            required=True,
            help=_(u'Dies sense resposta de la distribuïdora')
        ),
        'state_id': fields.many2one(
           'som.autoreclama.state',
           _(u'Estat actual'),
           required=True
        ),
        'next_state_id': fields.many2one(
           'som.autoreclama.state',
           _(u'Estat següent'),
           required=True
        ),
    }

    _defaults = {}


SomAutoreclamaStateCondition()
