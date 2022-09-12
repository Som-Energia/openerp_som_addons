# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from osv import osv, fields
from tools.translate import _
from oorq.decorators import job


## Class Task that describes the module and the task fields
class SomCrawlersTask(osv.osv):
    ## Module name
    _name = 'som.crawlers.task'
    ## Columns fields
    _columns = {
        'name': fields.char(_(u"Nom"), size=128, help=_("Nom de la tasca"),required=True,),
        'active': fields.boolean( string=_(u"Actiu"), help=_(u"Indica si la tasca està activa o no"),),
        'task_step_ids': fields.one2many('som.crawlers.task.step','task_id', string=_(u"Passos de la tasca")),
        'data_proxima_execucio':fields.datetime(_(u"Data proxima execució"),),
        'configuracio_id': fields.many2one('som.crawlers.config', 'Configuracio', help="Relacio de una configuracio amb la seva tasca",),
        'run_ids': fields.one2many('som.crawlers.result','task_id',string="Llistat d'execucions", help="Llista de execucions que ha realitzat la tasca",),
        'ultima_tasca_executada': fields.char(_(u"Darrer pas executat"), size=128, help=_("Darrer pas de tasca executat"),),
    }
    ## Default values of a column
    _defaults = {
        'active': lambda *a:False,
        'data_proxima_execucio':datetime.now().strftime("%Y-%m-%d_%H:%M"),
    }

    def id_del_portal_config(self,cursor,uid,id,context=None):
        classConfig = self.pool.get('som.crawlers.config')
        task_obj = self.browse(cursor,uid,id)
        config_obj = classConfig.browse(cursor,uid,task_obj.configuracio_id.id)
        return config_obj

    @job(queue="som_crawlers", timeout=1200)
    def executar_tasca_async(self, cursor, uid, id, context=None):
        self.executar_tasca(cursor, uid, id, context=context)

    def executar_tasca(self,cursor,uid,id,context=None):

        classresult = self.pool.get('som.crawlers.result')
        classTaskStep = self.pool.get('som.crawlers.task.step')
        task_obj = self.browse(cursor, uid, id)
        task_steps_list = task_obj.task_step_ids
        task_steps_list.sort(key=lambda x: x.sequence)
        result_id = classresult.create(cursor,uid,{'task_id': id,'data_i_hora_execucio': datetime.now().strftime("%Y-%m-%d_%H:%M")})

        for taskStep in task_steps_list:
            try:
                output = classTaskStep.executar_steps(cursor,uid,taskStep.id,result_id)
                classresult.write(cursor,uid, result_id, {'resultat': output})
            except Exception as e:
                classresult.write(cursor,uid, result_id, {'resultat': str(e)})
                break

        self.schedule_next_execution(cursor, uid, id, context)

    def schedule_next_execution(self, cursor, uid, id, context=None):
        ir_obj = self.pool.get('ir.model.data')
        cron_obj = self.pool.get('ir.cron')
        data_anterior = datetime.strptime(self.read(cursor, uid, id, ['data_proxima_execucio'])['data_proxima_execucio'], "%Y-%m-%d %H:%M:%S")
        data_proxima_exec = (datetime.now() + timedelta(days=1)).replace(
            hour=data_anterior.hour, minute=data_anterior.minute, second=data_anterior.second).strftime("%Y-%m-%d %H:%M:%S")
        #seguent data d'execucio
        self.write(cursor, uid, id,{'data_proxima_execucio': data_proxima_exec}, context)
        cron_id = ir_obj.get_object_reference(
            cursor, uid, 'som_crawlers', 'ir_cron_run_tasks_action'
        )[1]
        cron_obj.write(cursor, uid, cron_id, {'nextcall': data_proxima_exec}, context)

SomCrawlersTask()