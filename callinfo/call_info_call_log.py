# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import datetime
import re

class CallInfoCallLog(osv.osv):

    _name = 'call.info.call.log'


    def _normalize_phone_number(self, phone_number):
        clean_phone_number = re.sub(r'[ +-(),.]', '', phone_number)
        return phone_number.lstrip('0')

    def insert_call_log(self, cursor, uid, call_data, context=None):
        new_call = {
            'phone': self._normalize_phone_number(call_data['phone']),
            'partner_id': call_data['partner_id'],
            'contract_id': call_data['polissa_id']
            'date': datetime.now(),
            'categ_id': call_data['categ_id'],
            'comment': call_data['notes'],
            'user_id': call_data['user_id'],
        }
        if 'atc' in call_data:
            new_atc['atc_id'] = call_data['atc']

        return self.create(cursor, uid, new_call, context=context)

    _columns = {
        'phone': fields.char(
            _('Telèfon'),
            size=32,
            help=_('Telèfon associat a la trucada')
        ),
        'partner_id': fields.many2one(
            'res.partner',
            _('Client'),
            help=_('Client associat a la trucada')
        ),
        'contract_id': fields.many2one(
            'giscedata.polissa',
            _('Pòlissa'),
            help=_('Pòlissa associada a la trucada')
        ),
        'date': fields.datetime(
            _('Data'),
            required=True,
            help=_('Dia i hora de la trucada')
        ),
        'categ_id': fields.many2one(
            'crm.case.categ',
            _('Categoria'),
            required=True,
            help=_('Categoria de la trucada')
        ),
        'comment': fields.text(
            _(u'Comentari'),
            help=_(u"Explicació de la trucada")
        ),
        'atc_id': fields.many2one(
            'giscedata.atc',
            _(u'ATC'),
            help=_('Cas ATC creat amb la trucada - Reclamació')
        ),
        'user_id': fields.many2one(
            'res.users',
            _('Usuari'),
            required=True,
            help=_('Usuari que va atendre la trucada')
        )
    }

    _defaults = {
    }


CallInfoCallLog()
