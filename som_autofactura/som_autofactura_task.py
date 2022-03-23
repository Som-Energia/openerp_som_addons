# -*- coding: utf-8 -*-
from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
from time import sleep
from base_extended.base_extended import MultiprocessBackground
import ast

SECONDS_SLEEP = 300

class SomAutofacturaTask(osv.osv):

    _name = 'som.autofactura.task'

    @MultiprocessBackground.background(queue='background_somenergia')
    def action_execute_task(self, cursor, uid, ids, context):
        if isinstance(ids, list):
            ids = ids[0]
        step_obj = self.pool.get('som.autofactura.task.step')

        for step_id in step_obj.search(cursor, uid, [('task_id', '=' , ids), ('active','=', True)], order="sequence"):
            step = step_obj.browse(cursor, uid, step_id, context)
            step._execute_task(context=context)
            step._wait_until_task_done(context=context)

        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'name': fields.text(
            _(u"Nom"),
            help=_("Nom del pas")
        ),
        'active': fields.boolean(
            string=_(u'Actiu'),
            help=_(u"Indica si la tasca està activa o no")
        ),
    }

    _defaults = {
        'active': lambda *a: False,
    }


SomAutofacturaTask()


class SomAutofacturaTaskStep(osv.osv):

    _name = 'som.autofactura.task.step'

    def _execute_task(self, cursor, uid, ids, context):
        task = self.browse(cursor, uid, ids[0])
        logger = netsvc.Logger()

        logger.notifyChannel("som_autofactura", netsvc.LOG_INFO, "executing {}.{}".format(task.object_name.model, task.function))
        if 'wizard' in task.object_name.model:
            wiz_obj = self.pool.get(task.object_name.model)
            wiz_id = wiz_obj.create(cursor, uid, ast.literal_eval(task.params), context)
            wiz = wiz_obj.browse(cursor, uid, wiz_id)
            function = getattr(wiz, task.function)
            result = function(context=context)
            logger.notifyChannel("som_autofactura", netsvc.LOG_INFO, "executed {}.{}".format(task.object_name.model, task.function))

        elif '_button' in task.function:
            lot_obj = self.pool.get('giscedata.facturacio.lot')
            lot_ids = lot_obj.search(cursor, uid, [('state', '=', 'obert')])
            obj = self.pool.get(task.object_name.model)
            function = getattr(obj, task.function)
            context['validar_i_facturar'] = False
            result = function(cursor, uid, lot_ids, context)
            logger.notifyChannel("som_autofactura", netsvc.LOG_INFO, "executed {}.{}".format(task.object_name.model, task.function))
        else:
            logger.notifyChannel("som_autofactura", netsvc.LOG_INFO, "unknown task to execute {}.{}".format(task.object_name.model, task.function))

        return result

    def _wait_until_task_done(self, cursor, uid, ids, context):
        task = self.browse(cursor, uid, ids[0])
        logger = netsvc.Logger()
        logger.notifyChannel("som_autofactura", netsvc.LOG_INFO, "waiting for {}.{}".format(task.object_name.model, task.function))

        oorq_obj = self.pool.get('oorq.jobs.group')
        prev_work_not_finish = True
        while(prev_work_not_finish):
            prev_work_not_finish = oorq_obj.search(cursor, uid, [('active','=',True), ('name', 'ilike', task.autoworker_task_name)])
            sleep(SECONDS_SLEEP)

        if 'obrir_factures_button' in task.function:
            gff_obj = self.pool.get('giscedata.facturacio.factura')
            gff_draft = gff_obj.search(cursor, uid, [('state','=','draft')])
            gff_draft_old = gff_draft + 1
            while(gff_draft != gff_draft_old):
                gff_draft_old = gff_draft
                sleep(SECONDS_SLEEP)
                gff_draft = gff_obj.search(cursor, uid, [('state','=','draft')])

        logger.notifyChannel("som_autofactura", netsvc.LOG_INFO, "done {}.{}".format(task.object_name.model, task.function))
        return True

    _columns = {
        'name': fields.text(
            _(u"Nom"),
            help=_("Nom del pas")
        ),
        'sequence': fields.integer(
            _(u'Ordre'),
            required=True,
        ),
        'active': fields.boolean(
            string=_(u'Actiu'),
            help=_(u"Indica si la tasca està activa o no"),
            required=True,
        ),
        'object_name': fields.many2one('ir.model', 'Model'),
        'function': fields.text(
            _(u'Funció'),
            required=True,
        ),
        'params': fields.text(_(u"Paràmetres")),
        'autoworker_task_name': fields.text(_(u"Condicio d'acabar")),
        'task_id': fields.many2one('som.autofactura.task', _('Tasca'),
            select=True),
    }

    _defaults = {
        'sequence': lambda *a: 99,
        'active': lambda *a: False,
    }


SomAutofacturaTaskStep()