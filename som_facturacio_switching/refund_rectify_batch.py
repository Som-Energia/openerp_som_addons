# -*- coding: utf-8 -*-
from __future__ import absolute_import
import base64
import csv
from datetime import datetime, timedelta
from StringIO import StringIO
from osv import osv, fields
from tools.translate import _


INVOICE_DIFFERENCE_MAG_TOLERANCE = 0.02

REFUND_RECTIFY_BATCH_STATUS = [
    ("pending", "Pendent"),
    ("running", "Executant-se"),
    ("blocked", "Bloquejada"),
    ("done", "Finalitzada Ok"),
    ("failed", "Finalitzada Error"),
    ("cancelled", "Cancelada"),
]

REFUND_RECTIFY_BATCH_LINE_STATUS = [
    ("pending", "Pendent"),
    ("running", "Executant-se"),
    ("done", "Finalitzada Ok"),
    ("failed", "Finalitzada Error"),
    ("blocked", "Bloquejada"),
]


def _csv_value(value):
    if isinstance(value, unicode):
        return value.encode("utf-8")
    return str(value or "")


class RefundRectifyBatch(osv.osv):
    _name = "refund.rectify.batch"
    _description = "Refund and rectify F1 batch"
    _order = "create_date desc, id desc"

    _columns = {
        "name": fields.char("Reference", size=64, required=True, readonly=True),
        "polissa_id": fields.many2one("giscedata.polissa", "Polissa", required=True, readonly=True),
        "started_at": fields.datetime("Començada", readonly=True),
        "finished_at": fields.datetime("Finalitzada", readonly=True),
        "state": fields.selection(
            REFUND_RECTIFY_BATCH_STATUS, "Estat", required=True, readonly=True
        ),
        "total_lines": fields.integer("F1 totals", readonly=True),
        "completed_lines": fields.integer("F1 completats", readonly=True),
        "failed_lines": fields.integer("F1 erronis", readonly=True),
        "blocked_lines": fields.integer("F1 bloquejats", readonly=True),
        "summary": fields.text("Resum", readonly=True),
        "job_reference": fields.char("Job reference", size=128, readonly=True),
        "line_ids": fields.one2many(
            "refund.rectify.batch.line", "batch_id", "Linies", readonly=True
        ),
    }

    _defaults = {
        "state": lambda *a: "pending",
        "total_lines": lambda *a: 0,
        "completed_lines": lambda *a: 0,
        "failed_lines": lambda *a: 0,
        "blocked_lines": lambda *a: 0,
    }

    def create(self, cursor, uid, vals, context=None):
        batch_id = super(RefundRectifyBatch, self).create(cursor, uid, vals, context=context)
        self.write(cursor, uid, [batch_id], {"name": "F1_R-TASCA-%s" % batch_id}, context=context)
        return batch_id

    def create_batch(self, cursor, uid, polissa_id, f1_ids, context=None):
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        ordered_f1_ids = f1_obj.search(
            cursor, uid, [("id", "in", f1_ids)], order="fecha_factura_desde asc, id asc"
        )
        batch_id = self.create(
            cursor,
            uid,
            {
                "name": "/",
                "polissa_id": polissa_id,
                "total_lines": len(ordered_f1_ids),
                "summary": _("Tasca pendent creada. Encara no s'ha iniciat cap refacturació."),
            },
            context=context,
        )

        line_obj = self.pool.get("refund.rectify.batch.line")
        for sequence, f1_id in enumerate(ordered_f1_ids, 1):
            line_obj.create(
                cursor,
                uid,
                {"batch_id": batch_id, "f1_id": f1_id, "sequence": sequence},
                context=context,
            )
        return batch_id

    def _refresh_execution(self, cursor, uid, batch_id, context=None):
        """Persist progress, terminal state and the monitoring CSV from its lines."""
        line_obj = self.pool.get("refund.rectify.batch.line")
        line_ids = line_obj.search(
            cursor, uid, [("batch_id", "=", batch_id)], order="sequence asc, id asc",
            context=context
        )
        lines = line_obj.browse(cursor, uid, line_ids, context=context)
        counts = dict((state, 0) for state, unused in REFUND_RECTIFY_BATCH_LINE_STATUS)
        csv_file = StringIO()
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "sequence", "f1_id", "state", "invoices", "result", "error",
        ])
        for line in lines:
            counts[line.state] += 1
            csv_writer.writerow([
                line.sequence, line.f1_id.id, line.state,
                ",".join([str(invoice.id) for invoice in line.generated_invoice_ids]),
                _csv_value(line.result), _csv_value(line.error),
            ])
        batch = self.browse(cursor, uid, batch_id, context=context)
        state = batch.state
        if state != "cancelled":
            if counts["failed"]:
                state = "failed"
            elif counts["blocked"]:
                state = "blocked"
            elif counts["running"]:
                state = "running"
            elif counts["pending"]:
                state = "pending"
            else:
                state = "done"
        summary = "F1 totals: {total}. Completats: {done}. Erronis: {failed}. Bloquejats: {blocked}.".format(  # noqa: E501
            total=len(lines), done=counts["done"], failed=counts["failed"],
            blocked=counts["blocked"]
        )
        filename = "%s.csv" % batch.name
        attachment_vals = {
            "name": filename,
            "datas": base64.b64encode(csv_file.getvalue()),
            "datas_fname": filename,
            "res_model": self._name,
            "res_id": batch_id,
        }
        attachment_obj = self.pool.get("ir.attachment")
        attachment_ids = attachment_obj.search(
            cursor,
            uid,
            [("res_model", "=", self._name), ("res_id", "=", batch_id), ("name", "=", filename)],
            limit=1,
            context=context,
        )
        if attachment_ids:
            attachment_obj.write(cursor, uid, attachment_ids, attachment_vals, context=context)
        else:
            attachment_obj.create(cursor, uid, attachment_vals, context=context)
        vals = {
            "state": state,
            "total_lines": len(lines),
            "completed_lines": counts["done"],
            "failed_lines": counts["failed"],
            "blocked_lines": counts["blocked"],
            "summary": summary,
        }
        if state in ("done", "failed", "blocked", "cancelled"):
            vals["finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.write(cursor, uid, [batch_id], vals, context=context)
        return vals

    def process_batch_f1_lines(self, cursor, uid, batch_id, context=None):
        """Process batch lines serially, carrying the predecessor outcome."""
        line_obj = self.pool.get("refund.rectify.batch.line")

        context = context or {}
        self.write(cursor, uid, [batch_id], {
            "state": "running",
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": False,
        }, context=context)
        batch = self.browse(cursor, uid, batch_id, context=context)

        previous_f1_id = None
        predecessor_processed = False
        results = []
        for line in batch.line_ids:
            line_obj._mark_line_running(cursor, uid, line.id, context=context)
            try:
                result = line_obj.process_one_f1(
                    cursor, uid, line.f1_id.id, expected_polissa_id=batch.polissa_id.id,
                    previous_f1_id=previous_f1_id,
                    predecessor_processed=predecessor_processed, context=context
                )
            except Exception as error:
                line_obj._persist_line_outcome(
                    cursor, uid, line.id, error=error, context=context
                )
                raise
            line_obj._persist_line_outcome(
                cursor, uid, line.id, result=result, context=context
            )
            results.append(result)
            previous_f1_id = line.f1_id.id
            predecessor_processed = result["status"] == "processed"
        return results


RefundRectifyBatch()


class RefundRectifyBatchLine(osv.osv):
    _name = "refund.rectify.batch.line"
    _description = "Refund and rectify F1 batch line"
    _order = "batch_id, sequence, id"

    _columns = {
        "batch_id": fields.many2one(
            "refund.rectify.batch", "Tasca", required=True, ondelete="cascade", readonly=True
        ),
        "f1_id": fields.many2one(
            "giscedata.facturacio.importacio.linia", "F1", required=True, readonly=True
        ),
        "sequence": fields.integer("Ordre", required=True, readonly=True),
        "state": fields.selection(
            REFUND_RECTIFY_BATCH_LINE_STATUS, "Estat", required=True, readonly=True
        ),
        "started_at": fields.datetime("Començada", readonly=True),
        "finished_at": fields.datetime("Finalitzada", readonly=True),
        "generated_invoice_ids": fields.many2many(
            "giscedata.facturacio.factura",
            "refund_rectify_batch_line_factura_rel",
            "line_id",
            "factura_id",
            "Factures generades",
            readonly=True,
        ),
        "result": fields.text("Resultat", readonly=True),
        "error": fields.text("Error", readonly=True),
    }

    _defaults = {
        "state": lambda *a: "pending",
    }

    def _mark_line_running(self, cursor, uid, line_id, context=None):
        self.write(cursor, uid, [line_id], {
            "state": "running",
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": False,
        }, context=context)

    def _persist_line_outcome(self, cursor, uid, line_id, result=None, error=None, context=None):
        """Save a functional outcome or a technical failure for one batch line."""
        result = result or {}
        vals = {
            "state": "failed" if error else "done",
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": "\n".join(result.get("messages", [])),
            "error": str(error) if error else False,
            "generated_invoice_ids": [(6, 0, result.get("generated_invoice_ids", []))],
        }
        self.write(cursor, uid, [line_id], vals, context=context)
        batch_id = self.read(cursor, uid, line_id, ["batch_id"], context=context)["batch_id"][0]
        self.pool.get("refund.rectify.batch")._refresh_execution(
            cursor, uid, batch_id, context=context
        )

    # revisió manual a partir d'aquí
    # verificar que no son alucinacions

    def _get_factures_client_by_dates(
            self, cursor, uid, polissa_id, data_inici, data_final, context=None):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        invoice_ids = fact_obj.search(
            cursor,
            uid,
            [
                ("polissa_id", "=", polissa_id),
                ("type", "in", ["out_invoice", "out_refund"]),
                ("refund_by_id", "=", False),
                ("rectificative_type", "not in", ["B", "A"]),
                ("data_inici", "<", data_final),
                ("data_final", ">", data_inici),
            ],
            order="data_inici asc",
            context=context,
        )
        draft_invoice_ids = fact_obj.search(
            cursor, uid, [("id", "in", invoice_ids), ("state", "=", "draft")], context=context
        )
        message = ""
        if draft_invoice_ids:
            fact_obj.unlink(cursor, uid, draft_invoice_ids, context=context)
            message = "S'han eliminat {} factures en esborrany".format(len(draft_invoice_ids))
            invoice_ids = list(set(invoice_ids) - set(draft_invoice_ids))
        return invoice_ids, message, draft_invoice_ids

    def _get_f1_meter_ids(self, cursor, uid, f1, context=None):
        """Return the F1 meters, requiring one ERP meter for every serial."""
        meter_obj = self.pool.get("giscedata.lectures.comptador")
        serials = sorted(set([
            lectura.comptador for lectura in f1.importacio_lectures_ids
            if lectura.comptador
        ]))
        if not serials:
            raise osv.except_osv(_("Error"), _("L'F1 no té comptadors"))
        meter_context = (context or {}).copy()
        meter_context["active_test"] = False
        meter_ids = meter_obj.search(
            cursor,
            uid,
            [("polissa", "=", f1.polissa_id.id), ("name", "in", serials)],
            order="id asc",
            context=meter_context,
        )
        meters_by_serial = {}
        for meter in meter_obj.browse(cursor, uid, meter_ids, context=meter_context):
            meters_by_serial.setdefault(meter.name, []).append(meter.id)
        invalid_serials = [
            serial for serial in serials
            if len(meters_by_serial.get(serial, [])) != 1
        ]
        if invalid_serials:
            raise osv.except_osv(
                _("Error"),
                _("No es pot resoldre unívocament el comptador de l'F1: %s")
                % ", ".join(invalid_serials),
            )
        return sorted([meters_by_serial[serial][0] for serial in serials])

    def _get_reading_anchor_ids(
            self, cursor, uid, meter_ids, data_inici, data_final,
            context=None, reload_initial=True):
        """Return deterministic pool-reading anchors for all F1 meters."""
        lectura_pool_obj = self.pool.get("giscedata.lectures.lectura.pool")
        previous_date = (
            datetime.strptime(data_inici, "%Y-%m-%d") - timedelta(days=1)
        ).strftime("%Y-%m-%d")
        anchors = []
        copied_anchors = set()
        for meter_id in meter_ids:
            initial_reading_ids = []
            initial_date = data_inici
            if reload_initial:
                initial_reading_ids = lectura_pool_obj.search(
                    cursor,
                    uid,
                    [("comptador", "=", meter_id), ("name", "=", data_inici)],
                    order="id asc",
                    limit=1,
                    context=context,
                )
                if not initial_reading_ids:
                    initial_date = previous_date
                    initial_reading_ids = lectura_pool_obj.search(
                        cursor,
                        uid,
                        [("comptador", "=", meter_id), ("name", "=", previous_date)],
                        order="id asc",
                        limit=1,
                        context=context,
                    )
            final_reading_ids = lectura_pool_obj.search(
                cursor,
                uid,
                [("comptador", "=", meter_id), ("name", "=", data_final)],
                order="id asc",
                limit=1,
                context=context,
            )
            anchors_to_copy = [(data_final, final_reading_ids)]
            if reload_initial:
                anchors_to_copy.insert(0, (initial_date, initial_reading_ids))
            for anchor_date, reading_ids in anchors_to_copy:
                anchor = (meter_id, anchor_date)
                if reading_ids and anchor not in copied_anchors:
                    anchors.append(reading_ids[0])
                    copied_anchors.add(anchor)
        return anchors

    def _recarregar_lectures_between_dates(
            self, cursor, uid, meter_ids, data_inici, data_final,
            context=None, reload_initial=True):
        copy_wizard_obj = self.pool.get("wizard.copiar.lectura.pool.a.fact")
        anchor_ids = self._get_reading_anchor_ids(
            cursor, uid, meter_ids, data_inici, data_final,
            reload_initial=reload_initial, context=context
        )
        for lectura_id in anchor_ids:
            lectura_context = {"active_id": lectura_id, "active_ids": [lectura_id]}
            wizard_id = copy_wizard_obj.create(
                cursor, uid, {"overwrite": True}, context=lectura_context
            )
            copy_wizard_obj.action_copia_lectura(
                cursor, uid, [wizard_id], context=lectura_context
            )
        return len(anchor_ids)

    def _build_reading_anchor_plan(
            self, cursor, uid, f1, meter_ids, previous_f1_id=None,
            predecessor_processed=False, context=None):
        """Select the safe anchors for one F1 in a serial batch."""
        reload_initial = True
        if predecessor_processed and previous_f1_id:
            f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
            previous_f1 = f1_obj.browse(
                cursor, uid, previous_f1_id, context=context
            )
            previous_meter_ids = self._get_f1_meter_ids(
                cursor, uid, previous_f1, context=context
            )
            previous_final = datetime.strptime(
                previous_f1.fecha_factura_hasta, "%Y-%m-%d"
            ).date()
            current_initial = datetime.strptime(
                f1.fecha_factura_desde, "%Y-%m-%d"
            ).date()
            reload_initial = not (
                previous_meter_ids == meter_ids
                and previous_final + timedelta(days=1) == current_initial
            )
        return {"meter_ids": meter_ids, "reload_initial": reload_initial}

    def _refund_rectify_if_needed(self, cursor, uid, invoice_ids, context=None):
        wizard_obj = self.pool.get("wizard.ranas")
        wizard_context = {"active_ids": invoice_ids, "active_id": invoice_ids[0]}
        wizard_id = wizard_obj.create(cursor, uid, {}, context=wizard_context)
        return wizard_obj.action_rectificar(cursor, uid, wizard_id, context=wizard_context)

    def _get_invoice_total_mag(self, cursor, uid, invoice_id, context=None):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        product_obj = self.pool.get("product.product")
        mag_product_ids = product_obj.search(
            cursor, uid, [("default_code", "=", "RMAG")], context=context
        )
        invoice = fact_obj.browse(cursor, uid, invoice_id, context=context)
        mag = 0.0
        for energy_line in invoice.linies_energia:
            if energy_line.product_id.id in mag_product_ids:
                mag += energy_line.price_subtotal
        return mag

    def _delete_draft_invoices_if_needed(
            self, cursor, uid, generated_invoice_ids, source_invoice_ids, context=None):
        messages = []
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        generated_infos = fact_obj.read(
            cursor,
            uid,
            generated_invoice_ids,
            ["rectifying_id", "amount_untaxed", "invoice_id", "is_gkwh", "linies_generacio"],
            context=context,
        )
        for generated_info in generated_infos:
            generated_info["amount_untaxed_no_mag"] = (
                generated_info["amount_untaxed"]
                - self._get_invoice_total_mag(cursor, uid, generated_info["id"], context=context)
            )
        for source_invoice_id in source_invoice_ids:
            source_info = fact_obj.read(
                cursor,
                uid,
                source_invoice_id,
                ["invoice_id", "number", "is_gkwh", "linies_generacio"],
                context=context,
            )
            invoice_id = source_info["invoice_id"][0]
            ab_re_infos = filter(
                lambda info: info["rectifying_id"][0] == invoice_id, generated_infos
            )
            has_gkwh = any([info["is_gkwh"] for info in ab_re_infos])
            has_autoconsumption = any([info["linies_generacio"] for info in ab_re_infos])
            equal_amounts = len(set([info["amount_untaxed_no_mag"] for info in ab_re_infos])) == 1
            close_amounts = (
                len(ab_re_infos) == 2
                and abs(
                    ab_re_infos[0]["amount_untaxed_no_mag"]
                    - ab_re_infos[-1]["amount_untaxed_no_mag"]
                ) < INVOICE_DIFFERENCE_MAG_TOLERANCE
            )
            if equal_amounts or close_amounts:
                if source_info["linies_generacio"] or has_autoconsumption:
                    messages.append(
                        "Per la factura numero {} no s'esborren perquè alguna de les factures té autoconsum.".format(  # noqa: E501
                            source_info["number"]
                        )
                    )
                elif source_info["is_gkwh"] or has_gkwh:
                    messages.append(
                        "Per la factura numero {} no s'esborren perquè alguna de les factures té generationkwh.".format(  # noqa: E501
                            source_info["number"]
                        )
                    )
                else:
                    ab_re_ids = [info["id"] for info in ab_re_infos]
                    fact_obj.unlink(cursor, uid, ab_re_ids, context=context)
                    if equal_amounts:
                        messages.append(
                            "Per la factura numero {} les factures AB i RE tenen mateix import, s'esborren".format(  # noqa: E501
                                source_info["number"]
                            )
                        )
                    else:
                        messages.append(
                            "Per la factura numero {} les factures AB i RE tenen quasi mateix import, s'esborren".format(  # noqa: E501
                                source_info["number"]
                            )
                        )
                    generated_invoice_ids = list(set(generated_invoice_ids) - set(ab_re_ids))
            else:
                messages.append(
                    "Per la factura numero {} les factures AB i RE tenen import diferent.".format(  # noqa: E501
                        source_info["number"]
                    )
                )
        return messages, generated_invoice_ids

    def _write_f1_observation(self, cursor, uid, f1_id, text, context=None):
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        observations = f1_obj.read(
            cursor, uid, f1_id, ["user_observations"], context=context
        )["user_observations"] or ""
        f1_obj.write(
            cursor,
            uid,
            f1_id,
            {"user_observations": "{}\n{}".format(text, observations)},
            context=context,
        )

    def _write_refacturation_observation(self, cursor, uid, f1_id, messages, context=None):
        result_text = "\n".join(messages)
        if "factures AB i RE tenen mateix import, s'esborren" in result_text:
            difference = " Diferència 0"
        elif "les factures AB i RE tenen quasi mateix import" in result_text:
            difference = " Diferència +- 0"
        elif "les factures AB i RE tenen import diferent" in result_text:
            difference = " Ok"
        elif "generationkwh." in result_text:
            difference = " Té GkWh"
        elif "autoconsum." in result_text:
            difference = " Té Auto"
        else:
            difference = ""
        text = "F1 refacturat en data {}. Resultat:{}\n{}".format(
            datetime.today().strftime("%d-%m-%Y"), difference, result_text
        )
        self._write_f1_observation(cursor, uid, f1_id, text, context=context)

    def process_one_f1(
            self, cursor, uid, f1_id, expected_polissa_id=None,
            context=None, previous_f1_id=None, predecessor_processed=False):
        """Process one F1 in draft mode; transaction ownership belongs to the caller."""
        context = context or {}
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        f1_ids = f1_obj.search(cursor, uid, [("id", "=", f1_id)], limit=1, context=context)
        if not f1_ids:
            raise osv.except_osv(_("Error"), _("No existeix l'F1 a processar"))
        f1 = f1_obj.browse(cursor, uid, f1_ids[0], context=context)
        if not f1.polissa_id:
            raise osv.except_osv(_("Error"), _("L'F1 no té una pòlissa resolta"))
        polissa_id = f1.polissa_id.id
        if expected_polissa_id is not None and polissa_id != expected_polissa_id:
            raise osv.except_osv(
                _("Error"), _("La pòlissa de l'F1 no coincideix amb la de la tasca")
            )
        origin = f1.invoice_number_text
        result = {
            "status": "no_action",
            "f1_id": f1.id,
            "polissa_id": polissa_id,
            "origin": origin,
            "source_invoice_ids": [],
            "removed_draft_invoice_ids": [],
            "reloaded_reading_count": 0,
            "generated_invoice_ids": [],
            "messages": [],
            "observation_written": False,
        }
        if f1.type_factura != "R":
            result["messages"].append("F1 no és tipus rectificatiu. No s'actua.")
            return result
        if f1.polissa_id.facturacio_suspesa:
            result["messages"].append("Pòlissa amb facturació suspesa. No s'actua.")
            return result
        meter_ids = self._get_f1_meter_ids(cursor, uid, f1, context=context)
        source_invoice_ids, draft_message, removed_draft_invoice_ids = (
            self._get_factures_client_by_dates(
                cursor,
                uid,
                polissa_id,
                f1.fecha_factura_desde,
                f1.fecha_factura_hasta,
                context=context,
            )
        )
        result["source_invoice_ids"] = source_invoice_ids
        result["removed_draft_invoice_ids"] = removed_draft_invoice_ids
        if draft_message:
            result["messages"].append(draft_message)
        if not source_invoice_ids:
            result["messages"].append(
                "No té res per abonar i rectificar perquè no hi ha factura generada, no s'actua"
            )
            self._write_f1_observation(
                cursor, uid, f1.id,
                "F1 NO refacturat en data {} per falta de factura generada".format(
                    datetime.today().strftime("%d-%m-%Y")
                ),
                context=context,
            )
            result["observation_written"] = True
            return result
        reading_plan = self._build_reading_anchor_plan(
            cursor, uid, f1, meter_ids, previous_f1_id=previous_f1_id,
            predecessor_processed=predecessor_processed, context=context
        )
        reloaded_reading_count = self._recarregar_lectures_between_dates(
            cursor, uid, reading_plan["meter_ids"], f1.fecha_factura_desde,
            f1.fecha_factura_hasta,
            reload_initial=reading_plan["reload_initial"], context=context
        )
        result["reloaded_reading_count"] = reloaded_reading_count
        if not reloaded_reading_count:
            result["messages"].append("No té lectures per esborrar. No s'hi actua.")
            return result
        generated_invoice_ids = self._refund_rectify_if_needed(
            cursor, uid, source_invoice_ids, context=context
        )
        cleanup_messages, generated_invoice_ids = self._delete_draft_invoices_if_needed(
            cursor, uid, generated_invoice_ids, source_invoice_ids, context=context
        )
        result["status"] = "processed"
        result["generated_invoice_ids"] = generated_invoice_ids
        result["messages"].append(
            "S'han esborrat {} lectures de la pòlissa {} i s'han generat {} factures".format(
                reloaded_reading_count, f1.polissa_id.name, len(generated_invoice_ids)
            )
        )
        result["messages"] += cleanup_messages
        self._write_refacturation_observation(
            cursor, uid, f1.id, cleanup_messages, context=context
        )
        result["observation_written"] = True
        return result


RefundRectifyBatchLine()
