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

    def executar_tasques(self, cursor, uid, ids, context=None):
        #obtenim l'objecte tasca
        import pudb; pu.db

        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get('active_ids',[])

        for id in active_ids:
            #obtenim una tasca
            task_obj = self.browse(cursor, uid, id)
            task_steps_list = task_obj.task_step_ids
            task_steps_list.sort(key=lambda x: x.sequence)
            for taskStep in task_steps_list:
                function = getattr(self, taskStep.function)
                date = function(cursor,uid,taskStep.id,context)
                task_obj.write({'ultima_tasca_executada': str(taskStep.name)+ ' - ' + date})

        return {'type': 'ir.actions.act_window_close'}

    def executar_un_fitxer(self, cursor, uid,id, context=None):

        classresult = self.pool.get('som.crawlers.result')
        classTaskStep = self.pool.get('som.crawlers.task.step')
        taskStep = classTaskStep.browse(cursor,uid,id)
        taskStepParams = json.loads(taskStep.params)
        if taskStepParams.has_key('nom_fitxer'):
            output =os.system("python3 /home/somenergia/src/openerp_som_addons/som_crawlers/scripts//"
             + taskStepParams['nom_fitxer'])
            if output == 0:
                output = 'ok'
            elif output == 512:
                output = 'File or directory doesn\'t exist'
            else :
                output = 'Error while executing'

        else:
            output = 'Falta especificar nom fitxer'
        data_i_hora = datetime.now()
        classresult.create(cursor,uid,{'task_id': taskStep.task_id.id, 'data_i_hora_execucio': data_i_hora, 'resultat':output})
        return data_i_hora.strftime("%m/%d/%Y, %H:%M:%S")



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
            size=128,
            required=True,)

    }

SomCrawlersResult()