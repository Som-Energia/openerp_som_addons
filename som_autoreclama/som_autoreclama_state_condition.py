# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import som_autoreclama_state

class SomAutoreclamaStateCondition(osv.osv):

    _name = 'som.autoreclama.state.condition'
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
        'state_id': fields.many2one(
           'som.autoreclama.state',
           _(u'Estat'),
           required=True
        ),
    }

    _defaults = {}

SomAutoreclamaStateCondition()
