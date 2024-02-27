# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from autoworker import AutoWorker
from oorq.decorators import create_jobs_group

STATES = [("init", "Estat Inicial"), ("finished", "Estat Final")]


class WizardCrearLecuresCalculades(osv.osv_memory):
    _name = "wizard.crear.lectures.calculades"

    def create_lectures_async(self, cursor, uid, ids, pol_ids, context={}):
        pol_o = self.pool.get("giscedata.polissa")

        job_ids = []
        for _id in pol_ids:
            j = pol_o.crear_lectura_calculades_async(cursor, uid, _id, context)
            job_ids.append(j.id)
        create_jobs_group(
            cursor.dbname,
            uid,
            _("Calcular lectures CCH {} pòlisses").format(len(pol_ids)),
            "invoicing.facturacio_calculada",
            job_ids,
        )
        amax_proc = int(
            self.pool.get("res.config").get(
                cursor, uid, "facturacio_calculada_tasks_max_procs", "0"
            )
        )
        if not amax_proc:
            amax_proc = None
        aw = AutoWorker(
            queue="facturacio_calculada", default_result_ttl=24 * 3600, max_procs=amax_proc
        )
        aw.work()

    def crear_lectures_moure_lot(self, cursor, uid, ids, context=None):
        pol_o = self.pool.get("giscedata.polissa")
        if context.get("from_model", False) == "giscedata.polissa":
            pol_ids = context.get("active_ids", [])
            result = pol_o.crear_lectures_calculades(cursor, uid, pol_ids, context)
        else:
            imd_o = self.pool.get("ir.model.data")
            cat_id = imd_o.get_object_reference(
                cursor, uid, "som_facturacio_calculada", "cat_gp_factura_calc"
            )[1]

            pol_ids = pol_o.search(cursor, uid, [("category_id", "in", cat_id)])
            if pol_ids:
                self.create_lectures_async(cursor, uid, ids, pol_ids, context)
                result = ["S'ha creat la tasca en segon pla"]
            else:
                result = ["No hi ha cap pòlissa amb la categoria"]
        self.write(cursor, uid, ids, {"state": "finished", "info": "\n".join(result)})

    _columns = {
        "state": fields.selection(STATES, _(u"Estat del wizard")),
        "info": fields.text(u"Informació", readonly=True),
    }

    _defaults = {"state": "init", "info": lambda *a: ""}


WizardCrearLecuresCalculades()
