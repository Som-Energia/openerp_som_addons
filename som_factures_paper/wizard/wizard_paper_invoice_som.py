# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta
import json
import netsvc
import tempfile
import os
import tools
from cStringIO import StringIO
from zipfile import PyZipFile, ZIP_DEFLATED
import base64
from tools import config
from oorq.decorators import job
from oorq.oorq import JobsPool
import threading
import pooler
import csv


STATES = [
    ("init", "Estat Inicial"),
    ("info", "Informació de factures impresses"),
    ("working", "Generant factures"),
    ("done", "Estat Final"),
]


class ProgressJobsPool(JobsPool):
    def __init__(self, wizard):
        self.wizard = wizard
        super(ProgressJobsPool, self).__init__()

    @property
    def all_done(self):
        self.wizard.write({"progress": self.progress})
        return super(ProgressJobsPool, self).all_done


class WizardPaperInvoiceSom(osv.osv_memory):
    _name = "wizard.paper.invoice.som"

    _columns = {
        "state": fields.selection(STATES, _(u"Estat del wizard de imprimir report")),
        "date_from": fields.date("Data desde"),
        "date_to": fields.date("Data fins"),
        "info": fields.text("Informació", readonly=True),
        "invoice_ids": fields.text("Factures"),
        "file": fields.binary("Fitxer generat"),
        "file_name": fields.text("Nom del fitxer"),
        "progress": fields.float(u"Progrés general"),
    }

    _defaults = {
        "state": lambda *a: "init",
        "file_name": lambda *a: "factures.zip",
        "date_to": lambda *a: (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
    }

    def search_invoices(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        pol_obj = self.pool.get("giscedata.polissa")
        fact_obj = self.pool.get("giscedata.facturacio.factura")

        wiz = self.browse(cursor, uid, ids[0], context=context)

        ctxt = context.copy()
        ctxt["active_test"] = False
        pol_ids = pol_obj.search(cursor, uid, [("enviament", "!=", "email")], context=ctxt)
        fact_ids = fact_obj.search(
            cursor,
            uid,
            [
                ("polissa_id", "in", pol_ids),
                ("date_invoice", ">=", wiz.date_from),
                ("date_invoice", "<=", wiz.date_to),
                ("state", "in", ("open", "paid")),
                ("type", "in", ("out_refund", "out_invoice")),
            ],
            context=context,
        )

        fact_datas = fact_obj.read(cursor, uid, fact_ids, ["number"])
        fact_names = ", ".join([f["number"] for f in fact_datas])
        wiz.write(
            {
                "state": "info",
                "invoice_ids": json.dumps(fact_ids),
                "info": "Trobades {} polisses amb enviament postal.\nEs generanan {} pdf's de les seguents factures:\n{}".format(  # noqa: E501
                    len(pol_ids), len(fact_ids), fact_names
                ),
            }
        )

    def generate_invoices(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        gen_thread = threading.Thread(
            target=self.generate_invoices_threaded, args=(cursor, uid, ids, context)
        )
        gen_thread.start()
        self.write(cursor, uid, ids, {"state": "working"})
        return True

    def generate_invoices_threaded(self, cr, uid, ids, context=None):
        if not context:
            context = {}

        cursor = pooler.get_db(cr.dbname).cursor()

        wiz = self.browse(cursor, uid, ids[0], context=context)
        fact_ids = json.loads(wiz.invoice_ids)
        tmp_dir = tempfile.mkdtemp()

        failed_invoices, info_inv = self.generate_inv(cursor, uid, wiz, fact_ids, tmp_dir, context)
        clean_invoices = list(set(fact_ids) - set(failed_invoices))
        info_csv = self.generate_csv(
            cursor, uid, wiz, clean_invoices, tmp_dir, "Adreces.csv", context
        )
        info_reb = self.generate_reb(cursor, uid, wiz, clean_invoices, tmp_dir, context)

        wiz.write(
            {
                "state": "done",
                "file": self.get_zip_from_directory(tmp_dir, True),
                "info": wiz.info + "\n" + info_inv + "\n" + info_csv + "\n" + info_reb,
            }
        )

    def generate_inv(self, cursor, uid, wiz, fact_ids, dirname, context=None):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        report = "report.giscedata.facturacio.factura"
        j_pool = ProgressJobsPool(wiz)

        for factura_done, fact_id in enumerate(fact_ids):
            fact = fact_obj.browse(cursor, uid, fact_id, context=context)
            file_name = u"{} {} {}.pdf".format(
                fact.polissa_id.name,
                fact.number,
                fact.polissa_id.direccio_notificacio.name,
            ).encode("latin-1")
            j_pool.add_job(
                self.render_to_file(cursor, uid, [fact_id], report, dirname, file_name, context)
            )
            wiz.write({"progress": (float(factura_done + 1) / len(fact_ids)) * 98})

        j_pool.join()

        failed_invoice = []
        for status, result in j_pool.results.values():
            if not status:
                failed_invoice.extend(result)

        if failed_invoice:
            fact_data = fact_obj.read(cursor, uid, failed_invoice, ["number"])
            facts = ", ".join([f["number"] for f in fact_data])
            info = u"Les següents {} factures han tingut error: {}".format(
                len(failed_invoice), facts
            )
        else:
            info = u"{} factures generades correctament.".format(len(fact_ids))

        return failed_invoice, info

    @job(
        queue=config.get("som_factures_paper_render_queue", "poweremail_render"),
        result_ttl=24 * 3600,
    )
    def render_to_file(self, cursor, uid, fids, report, dirname, file_name, context=None):
        """Return a tuple of status (True: OK, False: Failed) and the invoice path."""
        if context is None:
            context = {}
        try:
            report = netsvc.service_exist(report)
            values = {"model": "giscedata.facturacio.factura", "id": fids, "report_type": "pdf"}
            content = report.create(cursor, uid, fids, values, context)[0]
            # Escriure report a "fitxer"
            fitxer_name = os.path.join(dirname, file_name)
            with open(fitxer_name, "wb") as f:
                f.write(content)
            return True, fids
        except Exception:
            import traceback

            traceback.print_exc()
            sentry = self.pool.get("sentry.setup")
            if sentry is not None:
                sentry.client.captureException()
            return False, fids

    def generate_csv(self, cursor, uid, wiz, fact_ids, dirname, file_name, context=None):
        def blank(thing):
            return thing if thing else ""

        to_sort = {}
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        for fact_id in fact_ids:
            fact = fact_obj.browse(cursor, uid, fact_id, context=context)
            name = "{}".format(fact.polissa_id.name)
            to_sort[name] = (
                fact.polissa_id.direccio_notificacio.name,
                fact.polissa_id.name,
                fact.polissa_id.direccio_notificacio.street,
                fact.polissa_id.direccio_notificacio.zip,
                fact.polissa_id.direccio_notificacio.city,
                blank(fact.polissa_id.direccio_notificacio.street2),
                blank(fact.polissa_id.direccio_notificacio.apartat_correus),
            )

        output = StringIO()
        writer = csv.writer(
            output,
            delimiter=";",
        )
        writer.writerow(
            [
                u"Persona notificacio",
                u"Polissa",
                u"Carrer",
                u"CP",
                u"Ciutat",
                u"Carrer alt",
                u"Apartat correus",
            ]
        )
        for k in sorted(to_sort.keys()):
            writer.writerow(to_sort[k])

        try:
            fitxer_name = "{}/{}".format(dirname, file_name)
            with open(fitxer_name, "wb") as f:
                f.write(output.getvalue())
        except Exception:
            import traceback

            traceback.print_exc()
            sentry = self.pool.get("sentry.setup")
            if sentry is not None:
                sentry.client.captureException()

        wiz.write({"progress": 99})
        return u"Generat csv amb {} files.".format(len(fact_ids))

    def generate_reb(self, cursor, uid, wiz, fact_ids, dirname, context=None):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        report = "report.giscedata.facturacio.factura.rebut"

        facts_with_rebs_ids = []
        for fact_id in fact_ids:
            fact = fact_obj.browse(cursor, uid, fact_id, context=context)
            if fact.polissa_id.postal_rebut:
                facts_with_rebs_ids.append(fact_id)

        if not facts_with_rebs_ids:
            return u"Cap rebut generat."

        j_pool = ProgressJobsPool(wiz)

        for fact_id in facts_with_rebs_ids:
            fact = fact_obj.browse(cursor, uid, fact_id, context=context)
            file_name = "{} {} {} rebut.pdf".format(
                fact.polissa_id.name,
                fact.number,
                fact.polissa_id.direccio_notificacio.name,
            )
            j_pool.add_job(
                self.render_to_file(cursor, uid, [fact_id], report, dirname, file_name, context)
            )

        wiz.write({"progress": 100})
        j_pool.join()

        failed_invoice = []
        for status, result in j_pool.results.values():
            if not status:
                failed_invoice.extend(result)

        if failed_invoice:
            fact_data = fact_obj.read(cursor, uid, failed_invoice, ["number"])
            facts = ", ".join([f["number"] for f in fact_data])
            info = u"Els següents {} rebuts han tingut error: {}".format(len(failed_invoice), facts)
        else:
            info = u"{} Rebuts generats correctament.".format(len(facts_with_rebs_ids))

        return info

    def get_zip_from_directory(self, directory, b64enc=True):
        def _zippy(archive, path):
            path = os.path.abspath(path)
            base = os.path.basename(path)
            for f in tools.osutil.listdir(path, True):
                archive.write(os.path.join(path, f), os.path.join(base, f))

        archname = StringIO()
        archive = PyZipFile(archname, "w", ZIP_DEFLATED)
        archive.writepy(directory)
        _zippy(archive, directory)
        archive.close()
        val = archname.getvalue()
        archname.close()

        if b64enc:
            val = base64.encodestring(val)

        return val


WizardPaperInvoiceSom()
