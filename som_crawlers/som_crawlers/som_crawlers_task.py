# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
class SomCrawlersTask(osv.osv):
    _name = 'som.crawlers.task'
    _columns = {
        'name': fields.char(_(u"Nom"), size=128, help=_("Nom de la tasca"),required=True,),
        'active': fields.boolean( string=_(u"Actiu"), help=_(u"Indica si la tasca està activa o no"),),
        'task_step_ids': fields.one2many('som.crawlers.task.step','task_id', string=_(u"Passos de la tasca")),
        'data_proxima_execucio':fields.datetime(_(u"Data proxima execució"),),
        'configuracio_id': fields.many2one('som.crawlers.config', 'Configuracio', help="Relacio de una configuracio amb la seva tasca",),
        #'run_ids': fields.one2many('som.crawlers.config','',string="Llistat d'execucions", help="Llista de execucions que ha realitzat la tasca",),
    }
    _defaults = {
        'active': lambda *a:False,
    }


SomCrawlersTask()

class SomCrawlersTaskStep(osv.osv):

    _name = 'som.crawlers.task.step'
    _order = 'sequence'

    _columns = {
        'name': fields.char(
            _(u"Nom"),
            help=_("Nom del pas"),
            size=128,
            required=True,
        ),
        'sequence': fields.integer(
            _(u'Ordre'),
            required=True,
        ),
        'params': fields.text(
            _(u"Paràmetres"),
            help=_("Path del fitxer a passar a la funció del model a executar"),
        ),
        'autoworker_task_name': fields.text(
            _(u"Condicio d'acabar"),
            help=_("Cua o procés que fa la tasca i al que hem d'esperar que acabi"),
        ),
         'task_id': fields.many2one(
            'som.crawlers.task',
            _('Tasca'),
            help=_("Tasca englobant"),
            select=True,
        ),
    }

    _defaults = {
        'sequence': lambda *a: 99,
        'name': lambda *a: 'nom_per_defecte',
    }

SomCrawlersTaskStep()
