# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from oorq.decorators import create_jobs_group
from autoworker import AutoWorker
import time


STATES = [("init", "Estat Inicial"), ("step", "Estat Segon"), ("finished", "Estat Final")]
INVOICE_TYPES = [
    ("in_invoice", "Factura de proveïdor"),
    ("in_refund", "Factura de proveïdor (abonadora)"),
    ("out_invoice", "Factura de client"),
    ("out_refund", "Factura de client (abonadora)"),
]
INVOICES_STATES = [
    ("draft", _("Esborrany")),
    ("open", _("Obertes")),
    ("paid", _("Realitzades")),
    ("cancel", _(u"Cancel·lades")),
    ("all", _("Totes")),
]


class WizardPaymentOrderAddInvoices(osv.osv_memory):
    _name = "wizard.payment.order.add.invoices"

    def add_invoices_to_payment_order(self, cursor, uid, ids, context=None):

        inv_obj = self.pool.get("account.invoice")

        wiz = self.browse(cursor, uid, ids[0])
        search_params = []

        search_params_relation = {
            "invoice_state": [("state", "=", wiz.invoice_state)],
            "init_date": [("date_due", ">=", wiz.init_date)],
            "end_date": [("date_due", "<=", wiz.end_date)],
            "invoice_type": [("type", "=", wiz.invoice_type)],
            "fiscal_position": [("fiscal_position", "=", wiz.fiscal_position.id)],
            "payment_type": [("payment_type", "=", wiz.payment_type.id)],
            "pending_state_text": [("pending_state", "like", "{}%".format(wiz.pending_state_text))],
        }

        for field in search_params_relation.keys():
            if getattr(wiz, field):
                search_params += search_params_relation[field]
        if not wiz.allow_grouped:
            search_params += [("group_move_id", "=", False)]
        if not wiz.allow_re:
            search_params += [("rectificative_type", "!=", "R")]

        res_ids = inv_obj.search(cursor, uid, search_params + [("payment_order_id", "=", False)])
        values = {
            "len_result": "La cerca ha trobat {} resultats".format(len(res_ids)),
            "state": "step",
            "total_facts_to_add": len(res_ids),
            "res_ids": res_ids,
        }
        self.write(cursor, uid, ids, values)

    def add_invoices_with_limit(self, cursor, uid, ids, context=None):
        self.browse(cursor, uid, ids[0])

        self.write(
            cursor,
            uid,
            ids,
            {
                "len_result": u"La tasca s'ha encuat de forma asíncrona",
                "state": "finished",
            },
        )
        self.async_add_invoices_with_limit(cursor, uid, ids, context)

    def async_add_invoices_with_limit(self, cursor, uid, ids, context=None):

        wiz = self.browse(cursor, uid, ids[0])
        inv_ids = wiz.res_ids
        order_id = wiz.order.id
        if len(inv_ids) > wiz.total_facts_to_add:
            inv_ids = inv_ids[: wiz.total_facts_to_add]

        order_obj = self.pool.get("payment.order")
        inv_obj = self.pool.get("account.invoice")
        order = order_obj.browse(cursor, uid, order_id)
        jobs_ids = []

        for inv_id in inv_ids:
            j = inv_obj.afegeix_a_remesa_async(cursor, uid, [inv_id], order_id, context)
            jobs_ids.append(j.id)

        create_jobs_group(
            cursor.dbname,
            uid,
            _(u"Remesa {} - afegint {} factures a la remesa").format(order.name, len(inv_ids)),
            "accounting.add_invoices_to_remesa",
            jobs_ids,
        )

        aw = AutoWorker(queue="add_invoices_to_remesa")
        aw.work()

    def show_job_groups_progress(self, cursor, uid, ids, context=None):
        return {
            "name": "Tasques de comptabilitat",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "oorq.jobs.group",
            "type": "ir.actions.act_window",
            "auto_refresh": 5,
            "domain": "[('internal','like','accounting.%')]",
        }

    _columns = {
        "state": fields.selection(STATES, _(u"Estat del wizard")),
        "order": fields.many2one("payment.order", "Remesa", select=True),
        "len_result": fields.char("Resultat de la cerca", size=256),
        "total_facts_to_add": fields.integer(
            _("Num. de factures a incloure"), help="Numero de factures per afegir a la remesa"
        ),
        "res_ids": fields.json("Dades d'us per l'assistent"),
        "pending_state_text": fields.char("Estat pendent", size=256),
        "init_date": fields.date(_("Data inici")),
        "end_date": fields.date(_("Data final")),
        "invoice_state": fields.selection([(False, "")] + INVOICES_STATES, _("Estat")),
        "invoice_type": fields.selection([(False, "")] + INVOICE_TYPES, _("Tipus")),
        "fiscal_position": fields.many2one("account.fiscal.position", "Posició Fiscal"),
        "payment_type": fields.many2one("payment.type", "Tipus de pagament"),
        "allow_grouped": fields.boolean(
            "Permetre agrupacions", help="Activar aquesta opció admet factures agrupades"
        ),
        "allow_re": fields.boolean(
            "Permetre rectificadores", help="Activar aquesta opció admet factures rectificadores"
        ),
    }

    _defaults = {
        "state": "init",
        "order": lambda self, cr, uid, context: context.get("active_id", False),
        "invoice_state": "open",
        "init_date": lambda *a: time.strftime("%Y-%m-%d"),
        "end_date": lambda *a: time.strftime("%Y-%m-%d"),
        "invoice_type": "out_invoice",
        "len_result": lambda *a: "",
        "allow_grouped": False,
        "allow_re": False,
    }


WizardPaymentOrderAddInvoices()
