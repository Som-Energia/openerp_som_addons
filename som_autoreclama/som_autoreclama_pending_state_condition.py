# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import som_autoreclama_pending_state

class SomAutoreclamaPendingStateCondition(osv.osv):

    _name = 'som.autoreclama.pending.state.condition'
    _rec_name = 'subtype_id'

    _columns = {
        'subtype_id': fields.many2one(
            "giscedata.subtipus.reclamacio",
            _(u"Subtipus"),
            required=True
        ),
        'days': fields.integer(
            _(u'Dies'),
            required=True
        ),
        'pending_state_id': fields.many2one(
           'som.autoreclama.pending.state',
           _(u'Estat pendent'),
           required=True
        ),
    }

    _defaults = {}

SomAutoreclamaPendingStateCondition()
