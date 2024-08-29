# -*- encoding: utf-8 -*-

from __future__ import absolute_import
from osv import osv, fields

from pytz import timezone

LOCAL_TZ = timezone('Europe/Madrid')


class SomActionMenuLogger(osv.Timescale):
    _name = 'som.action.menu.logger'
    _time_column = 'create_date'

    _columns = {
        'create_date': fields.datetime('Creation date', required=True),
        'act_window_id': fields.integer('Action Window', required=True),
    }


SomActionMenuLogger()


class SomActionWzrdLogger(osv.Timescale):
    _name = 'som.action.wzrd.logger'  # we need to avoid the word "wizard" to escape recursion
    _time_column = 'create_date'

    _columns = {
        'create_date': fields.datetime('Creation date', required=True),
        'model': fields.char('Wizard model', size=128, required=True)
    }


SomActionWzrdLogger()
