# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
import logging

logger = logging.getLogger('openerp.{}'.format(__name__))


class SomGurbCups(osv.osv):
    _name = "som.gurb.cups"
    _inherits = {'giscedata.cups.ps': 'cups_id'}
    _description = _('CUPS en grup de generació urbana')

    _columns = {
        'start_date': fields.date(u"Data entrada GURB", required=True),
        'end_date': fields.date(u"Data sortida GURB",),
        'gurb_id': fields.many2one("som.gurb", "GURB", required=True),
        'cups_id': fields.many2one('giscedata.cups.ps', 'CUPS'),
    }

SomGurbCups()