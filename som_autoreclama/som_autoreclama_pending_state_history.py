# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

class SomAutoreclamaPendingStateHistory(osv.osv):

    _name = 'som.autoreclama.pending.state.history'

    def get_this_model(self, cursor, uid, context=None):
        return self.pool.get('som.autoreclama.pending.state.history.{}'.format(self._namespace))

SomAutoreclamaPendingStateHistory()


class SomAutoreclamaPendingStateHistoryAtc(SomAutoreclamaPendingStateHistory):

    _name = 'som.autoreclama.pending.state.history.atc'
    _namespace = 'atc'

    _columns = {
        'pending_state_id': fields.many2one(
            'som.autoreclama.pending.state',
            u'Pending State',
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

SomAutoreclamaPendingStateHistoryAtc()
