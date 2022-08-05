# -*- coding: utf-8 -*-
from ast import Param
import subprocess
from datetime import datetime
from osv import osv, fields
from tools.translate import _
import os
import json

class SomCrawlersTask(osv.osv):
    _name = 'som.crawlers.task'
    _columns = {
        'name': fields.char(_(u"Nom"), size=128, help=_("Nom de la tasca"),required=True,),
        'active': fields.boolean( string=_(u"Actiu"), help=_(u"Indica si la tasca està activa o no"),),
        'task_step_ids': fields.one2many('som.crawlers.task.step','task_id', string=_(u"Passos de la tasca")),
        'data_proxima_execucio':fields.datetime(_(u"Data proxima execució"),),
        'configuracio_id': fields.many2one('som.crawlers.config', 'Configuracio', help="Relacio de una configuracio amb la seva tasca",),
        'run_ids': fields.one2many('som.crawlers.result','task_id',string="Llistat d'execucions", help="Llista de execucions que ha realitzat la tasca",),
        'ultima_tasca_executada': fields.char(_(u"Darrer pas executat"), size=128, help=_("Darrer pas de tasca executat"),),
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
        'function': fields.char(
            _(u'Funció'),
            help=_("Funció del model a executar"),
            size=256,
            required=True,
        ),
        'params': fields.text(
            _(u"Paràmetres"),
            help=_("Parametres a passar a la funció del model a executar"),
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
        'function': lambda *a: '',
        'name': lambda *a: 'nom_per_defecte',
    }

SomCrawlersTaskStep()

class SomCrawlersResult(osv.osv):
    _name= 'som.crawlers.result'

    _columns={

        'name': fields.char(_(u'Nom'), size=64, required=False,),
        'task_id': fields.many2one(
            'som.crawlers.task',
            _('Tasca'),
            help=_('Nom de la tasca'),
            select=True,
        ),
        'data_i_hora_execucio': fields.datetime(
            _(u"Data i hora de l'execució"),),
        'resultat': fields.char(
            _(u"Resultat"),
            help=_("Resultat de l'execució"),
            size=512,),
        'zip_name':fields.many2one('ir.attachment', _(u"Fitxer adjunt"),)

    }


SomCrawlersResult()
