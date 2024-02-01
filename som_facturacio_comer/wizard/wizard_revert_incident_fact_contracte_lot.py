# -*- encoding: utf-8 -*-
import netsvc
from osv import osv, fields
from tools.translate import _
from oorq.decorators import job, create_jobs_group
from autoworker import AutoWorker


class WizardRevertIncidentFactCLot(osv.osv_memory):

    _name = "wizard.revert.incident.fact.c_lot"

    @job(queue="delete_invoices")
    def delete_lot_factures_lectures_async(
        self, cursor, uid, wiz_id, pol_id, lot_id, c_lot_id, context={}
    ):
        self.delete_lot_factures_lectures(cursor, uid, wiz_id, pol_id, lot_id, c_lot_id, context)

    def delete_lot_factures_lectures(
        self, cursor, uid, wiz_id, pol_id, lot_id, c_lot_id, context={}
    ):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")
        lect_obj = self.pool.get("giscedata.lectures.lectura")
        lect_pot_obj = self.pool.get("giscedata.lectures.potencia")
        c_lot_obj = self.pool.get("giscedata.facturacio.contracte_lot")

        fact_ids = fact_obj.search(
            cursor,
            uid,
            [("lot_facturacio", "=", lot_id), ("polissa_id", "=", pol_id), ("state", "=", "draft")],
        )
        if fact_ids:
            fact_obj.unlink(cursor, uid, fact_ids)

        if context.get("delete_lectures", False):
            search_params = [
                ("comptador.polissa", "=", pol_id),
            ]
            data_ultima_lectura = pol_obj.read(cursor, uid, pol_id, ["data_ultima_lectura"])[
                "data_ultima_lectura"
            ]
            if data_ultima_lectura:
                search_params.append(("name", ">", data_ultima_lectura))
            lectures_ids = lect_obj.search(cursor, uid, search_params)

            if lectures_ids:
                lect_obj.unlink(cursor, uid, lectures_ids)

            lectures_pot_ids = lect_pot_obj.search(cursor, uid, search_params)
            if lectures_pot_ids:
                lect_pot_obj.unlink(cursor, uid, lectures_pot_ids)

        c_lot_obj.wkf_obert(cursor, uid, [c_lot_id], context={"validate": False, "from_lot": True})

    def do_action(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, ids[0])
        context.update({"delete_lectures": wiz.delete_lectures})

        selected_ids = context.get("active_ids", [])
        c_lot_obj = self.pool.get("giscedata.facturacio.contracte_lot")
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        error_msg = []
        job_ids = []

        logger = netsvc.Logger()

        for _id in selected_ids:
            c_lot = c_lot_obj.browse(cursor, uid, _id)
            if c_lot.lot_id.state != "obert":
                raise osv.except_osv(_("Error!"), _("El lot de facturació no està obert"))

            if not c_lot.polissa_id.data_ultima_lectura:
                fact_ids = fact_obj.search(
                    cursor,
                    uid,
                    [
                        ("polissa_id", "=", c_lot.polissa_id.id),
                        ("type", "=", "out_invoice"),
                        "|",
                        ("lot_facturacio", "!=", c_lot.lot_id.id),
                        ("lot_facturacio", "=", False),
                    ],
                    limit=1,
                )

                if fact_ids:
                    error_msg.append(
                        u"Pòlissa {} té factures però no té Data última lectura facturada Real. No s'hi actua\n".format(
                            c_lot.polissa_id.id
                        )
                    )
                    continue
            job = self.delete_lot_factures_lectures_async(
                cursor, uid, ids[0], c_lot.polissa_id.id, c_lot.lot_id.id, _id, context
            )
            job_ids.append(job.id)

        if job_ids:
            # Create a jobs_group to see the status of the operation
            create_jobs_group(
                cursor.dbname,
                uid,
                _(
                    "Eliminar factures i reobrir {0} pòlisses amb incidència (eliminar lectures: {1})."
                ).format(len(job_ids), context["delete_lectures"]),
                "facturacio_tasks.delete_invoices",
                job_ids,
            )
            amax_proc = int(
                self.pool.get("res.config").get(
                    cursor, uid, "facturacio_tasks_delete_invoices_tasks_max_procs", "0"
                )
            )
            if not amax_proc:
                amax_proc = None
            try:
                aw = AutoWorker(
                    queue="delete_invoices", default_result_ttl=24 * 3600, max_procs=amax_proc
                )
                aw.work()
            except ValueError:
                logger.notifyChannel(
                    "objects",
                    netsvc.LOG_WARNING,
                    "Número de procesos no vàlid ({}). No s'arrencarà "
                    "cap autoworker".format(amax_proc),
                )
        error_msg = "\n".join(error_msg)
        self.write(
            cursor,
            uid,
            [wiz.id],
            {
                "state": "end",
                "info": u"Pòlisses on actuar: {}\n{}\n\n Errors:\n{}".format(
                    len(job_ids), "-" * 10, error_msg
                ),
            },
        )

    _columns = {
        "state": fields.selection([("init", "Initial"), ("end", "End")], "State"),
        "delete_lectures": fields.boolean(
            _("Delete lectures.lectura and lectures.potencia from comptador")
        ),
        "info": fields.text(_("Informació")),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardRevertIncidentFactCLot()
