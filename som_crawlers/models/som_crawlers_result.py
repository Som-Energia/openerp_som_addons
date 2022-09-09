# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


# Class Result that describes the module and result fields
class SomCrawlersResult(osv.osv):
    # Module name
    _name= 'som.crawlers.result'

    # Column fields
    _columns={

        'name': fields.char(_(u'Funció'), size=64, required=False,),
        'task_id': fields.many2one(
            'som.crawlers.task',
            _('Tasca'),
            help=_('Nom de la tasca'),
            select=True,
        ),
        'data_i_hora_execucio': fields.datetime(
            _(u"Data i hora de l'execució"),),
        'resultat': fields.text(
            _(u"Resultat"),
            help=_("Resultat de l'execució"),
        ),
        'zip_name':fields.many2one('ir.attachment', _(u"Fitxer adjunt"),
        ),

    }
SomCrawlersResult()
