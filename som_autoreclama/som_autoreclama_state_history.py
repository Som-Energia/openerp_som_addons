# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import date


class SomAutoreclamaStateHistory(osv.osv):

    _name = 'som.autoreclama.state.history'

    def get_this_model(self, cursor, uid, context=None):
        return self.pool.get('som.autoreclama.state.history.{}'.format(self._namespace))


SomAutoreclamaStateHistory()


class SomAutoreclamaStateHistoryAtc(SomAutoreclamaStateHistory):

    _name = 'som.autoreclama.state.history.atc'
    _namespace = 'atc'

    def historize(self, cursor, uid, atc_id, next_state_id, current_date, generated_atc_id, context=None):
        if not current_date:
            current_date = date.today().strftime("%Y-%m-%d")

        h_ids = self.search(cursor, uid, [
            ('atc_id', '=', atc_id),
            ('end_date', '=', False),
            ],
            context=context
        )
        if h_ids:
            self.write(cursor, uid, h_ids,
                {'end_date': current_date},
                context=context
            )

        new_atc = {
            'atc_id': atc_id,
            'state_id': next_state_id,
            'change_date': current_date,
            'end_date': False,
        }
        if generated_atc_id:
            new_atc['generated_atc_id'] = generated_atc_id

        return self.create(cursor, uid, new_atc, context=context)

    _columns = {
        'state_id': fields.many2one(
            'som.autoreclama.state',
            _(u'State'),
            required=False
        ),
        'change_date': fields.date(
            _(u'Change Date'),
            select=True,
            readonly=True
        ),
        'end_date': fields.date(
            _(u'End Date'),
            select=True,
            readonly=True
        ),
        'atc_id': fields.many2one(
            'giscedata.atc',
            _(u'ATC'),
            readonly=True,
            ondelete="set null"
        ),
        'generated_atc_id': fields.many2one(
            'giscedata.atc',
            _(u'Cas ATC generat'),
            readonly=True,
            ondelete="set null"
        )
    }
    _order = 'end_date desc, id desc'


SomAutoreclamaStateHistoryAtc()
