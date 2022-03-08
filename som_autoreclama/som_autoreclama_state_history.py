# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

class SomAutoreclamaStateHistory(osv.osv):

    _name = 'som.autoreclama.state.history'

    def get_this_model(self, cursor, uid, context=None):
        return self.pool.get('som.autoreclama.state.history.{}'.format(self._namespace))

SomAutoreclamaStateHistory()


class SomAutoreclamaStateHistoryAtc(SomAutoreclamaStateHistory):

    _name = 'som.autoreclama.state.history.atc'
    _namespace = 'atc'

    _columns = {
        'autoreclama_state_id': fields.many2one(
            'som.autoreclama.state',
            u'State',
            required=False
        ),
        'change_date': fields.date(
            u'Change Date',
            select=True,
            readonly=True
        ),
        'end_date': fields.date(
            u'End Date',
            select=True,
            readonly=True
        ),
        'atc_id': fields.many2one(
            'giscedata.atc',
            u'ATC',
            readonly=True,
            ondelete="set null"
        )
    }
    _order = 'end_date desc, id desc'

SomAutoreclamaStateHistoryAtc()
