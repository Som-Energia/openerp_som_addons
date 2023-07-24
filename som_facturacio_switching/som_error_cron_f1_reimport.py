# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class SomErrorCronF1Reimport(osv.osv):
    _name = 'som.error.cron.f1.reimport'

    _columns = {
        'code': fields.many2one(
            'giscedata.facturacio.switching.error.template', 'Codis d\'error de F1'
        ),
        'text': fields.text(
            _(u"Text"),
            help=_("Text del error al F1 importat erroniament"),
        ),
        'active': fields.boolean(
            string=_(u'Actiu'),
            help=_(u"Indica si l'error es reimportarà al cron o no"),
            required=True
        ),


    }


SomErrorCronF1Reimport()
