# -*- encoding: utf-8 -*-
import pooler
from osv import osv, fields
from datetime import datetime, timedelta
import json
import csv
import base64
from StringIO import StringIO
from tools.translate import _


INVOICE_DIFFERENCE_MAG_TOLERANCE = 0.02


def get_today():
    return datetime.today().strftime("%d-%m-%Y")


class WizardRefundRectifyFromOrigin(osv.osv_memory):

    _name = "wizard.refund.rectify.from.origin"

    def send_polissa_mail(self, cursor, uid, ids, pol_id, is_positive_amount, context):
        wiz = self.browse(cursor, uid, ids[0])
        plantilla = (
            wiz.email_template_to_pay if is_positive_amount else wiz.email_template_to_refund
        )

        pem_send_wo = self.pool.get("poweremail.send.wizard")
        ctx = {
            "active_ids": [pol_id],
            "active_id": pol_id,
            "template_id": plantilla.id,
            "src_model": "giscedata.polissa",
            "src_rec_ids": [pol_id],
            "from": plantilla.enforce_from_account.id,
            "state": "single",
            "priority": 0,
        }
        params = {
            "state": "single",
            "priority": 0,
            "from": plantilla.enforce_from_account.id,
        }

        wz_id = pem_send_wo.create(cursor, uid, params, ctx)
        pem_send_wo.send_mail(cursor, uid, [wz_id], ctx)

    def is_positive_total_grouped_amount(self, cursor, uid, facts_created_ids, context):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        fact_datas = fact_obj.read(
            cursor, uid, facts_created_ids, ["amount_total", "type"], context
        )
        amount_total = sum(
            fact_data["amount_total"] * (1 if fact_data["type"] == "out_invoice" else -1)
            for fact_data in fact_datas
        )
        return amount_total >= 0.0

    def get_factures_client_by_dates(
        self, cursor, uid, ids, pol_id, data_inici, data_final, context={}
    ):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        msg = ""
        facts_cli_ids = fact_obj.search(
            cursor,
            uid,
            [
                ("polissa_id", "=", pol_id),
                ("type", "in", ["out_invoice", "out_refund"]),
                ("refund_by_id", "=", False),
                ("rectificative_type", "not in", ["B", "A"]),
                ("data_inici", "<", data_final),
                ("data_final", ">", data_inici),
            ],
            order="data_inici asc",
        )

        f_cli_rectificar_draft = fact_obj.search(
            cursor, uid, [("id", "in", facts_cli_ids), ("state", "=", "draft")]
        )
        if f_cli_rectificar_draft:
            fact_obj.unlink(cursor, uid, f_cli_rectificar_draft)
            msg = "S'han eliminat {} factures en esborrany".format(len(f_cli_rectificar_draft))
            facts_cli_ids = list(set(facts_cli_ids) - set(f_cli_rectificar_draft))
        return facts_cli_ids, msg

    def recarregar_lectures_between_dates(
        self, cursor, uid, ids, pol_id, data_inici, data_final, context={}
    ):
        pol_obj = self.pool.get("giscedata.polissa")
        lect_pool_obj = self.pool.get("giscedata.lectures.lectura.pool")
        copia_lect_wiz_o = self.pool.get("wizard.copiar.lectura.pool.a.fact")

        polissa = pol_obj.browse(cursor, uid, pol_id)
        data_lectura_anterior = (
            datetime.strptime(data_inici, "%Y-%m-%d") - timedelta(days=1)
        ).strftime("%Y-%m-%d")

        lect_prev_id = lect_pool_obj.search(
            cursor,
            uid,
            [
                ("comptador", "in", [x.id for x in polissa.comptadors]),
                ("name", "in", [data_lectura_anterior, data_inici]),
            ],
            limit=1,
        )

        lect_final_id = lect_pool_obj.search(
            cursor,
            uid,
            [("comptador", "in", [x.id for x in polissa.comptadors]), ("name", "=", data_final)],
            limit=1,
        )

        for lect_id in lect_prev_id + lect_final_id:
            context = {"active_id": lect_id, "active_ids": [lect_id]}
            wiz_id = copia_lect_wiz_o.create(cursor, uid, {"overwrite": True}, context=context)
            copia_lect_wiz_o.action_copia_lectura(cursor, uid, [wiz_id], context=context)

        return len(lect_prev_id + lect_final_id)

    def refund_rectify_if_needed(self, cursor, uid, f_ids, context={}):
        wiz_ranas_o = self.pool.get("wizard.ranas")

        ctx = {"active_ids": f_ids, "active_id": f_ids[0]}
        wiz_id = wiz_ranas_o.create(cursor, uid, {}, context=ctx)
        fres_resultat = wiz_ranas_o.action_rectificar(cursor, uid, wiz_id, context=ctx)
        return fres_resultat

    def get_invoice_total_mag(self, cursor, uid, f_id, context={}):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        product_obj = self.pool.get("product.product")
        mag_product_ids = product_obj.search(cursor, uid, [("default_code", "=", "RMAG")])

        fact = fact_obj.browse(cursor, uid, f_id, context)
        mag = 0.0
        for energy_line in fact.linies_energia:
            if energy_line.product_id.id in mag_product_ids:
                mag += energy_line.price_subtotal

        return mag

    def delete_draft_invoices_if_needed(self, cursor, uid, fres_resultat, f_ids, context={}):
        msg = []
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        f_res_info = fact_obj.read(
            cursor,
            uid,
            fres_resultat,
            ["rectifying_id", "amount_untaxed", "invoice_id", "is_gkwh", "linies_generacio"],
        )
        for f_res in f_res_info:
            mag = self.get_invoice_total_mag(cursor, uid, f_res["id"], context)
            f_res["amount_untaxed_no_mag"] = f_res["amount_untaxed"] - mag

        # Eliminem les que no cal rectificar (import AB == import RE)
        for initial_id in f_ids:
            inv_initial_info = fact_obj.read(
                cursor, uid, initial_id, ["invoice_id", "number", "is_gkwh", "linies_generacio"]
            )
            inv_id = inv_initial_info["invoice_id"][0]
            re_ab_fact_info = filter(lambda x: x["rectifying_id"][0] == inv_id, f_res_info)
            has_gkwh = any([x["is_gkwh"] for x in re_ab_fact_info])
            has_autoconsumption = any([x["linies_generacio"] for x in re_ab_fact_info])

            if len(set([x["amount_untaxed_no_mag"] for x in re_ab_fact_info])) == 1:
                if inv_initial_info["linies_generacio"] or has_autoconsumption:
                    msg.append(
                        "Per la factura numero {} no s'esborren perquè alguna de les factures té autoconsum.".format(  # noqa: E501
                            inv_initial_info["number"]
                        )
                    )
                elif inv_initial_info["is_gkwh"] or has_gkwh:
                    msg.append(
                        "Per la factura numero {} no s'esborren perquè alguna de les factures té generationkwh.".format(  # noqa: E501
                            inv_initial_info["number"]
                        )
                    )
                else:
                    ab_re_ids = [x["id"] for x in re_ab_fact_info]
                    fact_obj.unlink(cursor, uid, ab_re_ids)
                    msg.append(
                        "Per la factura numero {} les factures AB i RE tenen mateix import, s'esborren".format(  # noqa: E501
                            inv_initial_info["number"]
                        )
                    )
                    fres_resultat = list(set(fres_resultat) - set(ab_re_ids))
            elif (
                len(re_ab_fact_info) == 2
                and abs(
                    re_ab_fact_info[0]["amount_untaxed_no_mag"]
                    - re_ab_fact_info[-1]["amount_untaxed_no_mag"]
                )
                < INVOICE_DIFFERENCE_MAG_TOLERANCE
            ):
                if inv_initial_info["linies_generacio"] or has_autoconsumption:
                    msg.append(
                        "Per la factura numero {} no s'esborren perquè alguna de les factures té autoconsum.".format(  # noqa: E501
                            inv_initial_info["number"]
                        )
                    )
                elif inv_initial_info["is_gkwh"] or has_gkwh:
                    msg.append(
                        "Per la factura numero {} no s'esborren perquè alguna de les factures té generationkwh.".format(  # noqa: E501
                            inv_initial_info["number"]
                        )
                    )
                else:
                    ab_re_ids = [x["id"] for x in re_ab_fact_info]
                    fact_obj.unlink(cursor, uid, ab_re_ids)
                    msg.append(
                        "Per la factura numero {} les factures AB i RE tenen quasi mateix import, s'esborren".format(  # noqa: E501
                            inv_initial_info["number"]
                        )
                    )
                    fres_resultat = list(set(fres_resultat) - set(ab_re_ids))
            else:
                msg.append(
                    "Per la factura numero {} les factures AB i RE tenen import diferent.".format(
                        inv_initial_info["number"]
                    )
                )

        return msg, fres_resultat

    def check_max_amount(self, cursor, uid, ids, facts_ids, max_amount, context):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        for _id in facts_ids:
            factura = fact_obj.browse(cursor, uid, _id)
            if factura.type == "out_refund":
                continue
            if factura.amount_total > max_amount:
                return True

    def open_group_invoices(
        self, cursor, uid, ids, facts_created, payment_order_id, action, context={}
    ):

        wiz_ag_o = self.pool.get("wizard.group.invoices.payment")
        fact_obj = self.pool.get("giscedata.facturacio.factura")

        db = pooler.get_db_only(cursor.dbname)
        tmp_cr = db.cursor()
        try:
            fact_infos = fact_obj.read(cursor, uid, facts_created, ["id", "date_invoice"])
            sorted_factures = sorted(fact_infos, key=lambda f: f["date_invoice"])
            for factura in sorted_factures:
                factura_id = factura["id"]
                fact_obj.invoice_open(cursor, uid, [factura_id], context=context)

            tmp_cr.commit()
        except Exception:
            tmp_cr.rollback()
            return False, "Error en obrir les factures, no continua el procés"
        finally:
            tmp_cr.close()

        if action == "open":
            return True, "S'han obert {} factures.".format(len(sorted_factures))

        agrupar_ctx = {
            "active_id": facts_created[0],
            "active_ids": facts_created,
            "model": "giscedata.facturacio.factura",
        }
        wiz_id = wiz_ag_o.create(cursor, uid, {}, context=agrupar_ctx)
        wiz = wiz_ag_o.browse(cursor, uid, wiz_id)
        total_import = wiz.amount_total
        if wiz.amount_total == 0:
            return False, "L'agrupació de factures fan un total de 0. S'atura el procés."

        elif total_import < 0:
            total_import = wiz.amount_total
            res = wiz_ag_o.agrupar_remesar(cursor, uid, [wiz.id], context=agrupar_ctx)
            if action == "open-group":
                return True, "S'han obert i agrupat {} factures que sumen {}.".format(
                    len(sorted_factures), total_import
                )
            remesar_ctx = res["context"]
            wiz_remesar_o = self.pool.get(res["res_model"])
            wiz_remesa_id = wiz_remesar_o.create(
                cursor, uid, {"tipus": "payable", "order": payment_order_id}, context=remesar_ctx
            )
            wiz_remesar_o.action_afegir_factures(cursor, uid, wiz_remesa_id, context=remesar_ctx)
            return (
                True,
                "S'han agrupat les factures i s'han remesat, ja que l'import agrupat és {}".format(
                    total_import
                ),
            )
        else:
            wiz_ag_o.group_invoices(cursor, uid, [wiz.id], context=agrupar_ctx)
            return True, "S'han agrupat les factures, l'import agrupat és {}".format(total_import)

    def write_report(self, cursor, uid, ids, fact_csv_result, context):
        wizard = self.browse(cursor, uid, ids[0])
        csv_file = StringIO()
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow(["Origen", "Pòlissa", "Resultat"])
        writer.writerows(fact_csv_result)
        res_file = base64.b64encode(csv_file.getvalue())
        datetime.today().strftime("%Y%m%d")
        wizard.write(
            {
                "report_file": res_file,
            }
        )
        csv_file.close()

    def save_info_into_f1_after_refacturacio(self, cursor, uid, f1_refacturats, context):
        text = "F1 refacturat en data {}".format(datetime.today().strftime("%d-%m-%Y"))
        for f1_data in f1_refacturats:
            f1_id = f1_data["id"]
            f1_str = "\n".join(f1_data["refund_result"])
            if "factures AB i RE tenen mateix import, s'esborren" in f1_str:
                diff = " Diferència 0"
            elif "les factures AB i RE tenen quasi mateix import" in f1_str:
                diff = " Diferència +- 0"
            elif "les factures AB i RE tenen import diferent" in f1_str:
                diff = " Ok"
            elif "generationkwh." in f1_str:
                diff = " Té GkWh"
            elif "autoconsum." in f1_str:
                diff = " Té Auto"
            else:
                diff = ""

            message = "{}. Resultat:{}\n{}".format(text, diff, f1_str)
            self.add_f1_observation(cursor, uid, f1_id, message, context)

    def add_f1_observation(self, cursor, uid, f1_id, text, context):
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        obs = (
            f1_obj.read(cursor, uid, f1_id, ["user_observations"], context=context)[
                "user_observations"
            ]
            or ""
        )
        f1_obj.write(cursor, uid, f1_id, {"user_observations": "{}\n{}".format(text, obs)})

    def open_polissa_invoices_send_mail(self, cursor, uid, ids, facts_by_polissa, context={}):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        pol_obj = self.pool.get("giscedata.polissa")
        wiz = self.browse(cursor, uid, ids[0])
        msg = []
        fact_csv_result = []
        for pol_name, facts_created in facts_by_polissa.items():
            if not facts_created:
                continue
            pol_id = pol_obj.search(
                cursor, uid, [("name", "=", pol_name)], context={"active_test": False}
            )[0]
            res = False

            if wiz.actions != "draft":
                res, msg_open = self.open_group_invoices(
                    cursor, uid, ids, facts_created, wiz.order.id, wiz.actions, context
                )
                msg.append(
                    "S'han obert les factures de la pòlissa {}. {}".format(pol_name, msg_open)
                )
            if res and wiz.actions == "open-group-order-send":
                is_positive_amount = self.is_positive_total_grouped_amount(
                    cursor, uid, facts_created, context
                )
                self.send_polissa_mail(cursor, uid, ids, pol_id, is_positive_amount, context)
                msg.append(
                    "S'ha enviat el correu per {} a la pòlissa {}.".format(
                        "pagar" if is_positive_amount else "cobrar", pol_name
                    )
                )
            fact_csv_result.append(
                [
                    "",
                    pol_name,
                    "Ha arribat al final del procés (obrir {} factures: {}, enviar correu: {}).".format(  # noqa: E501
                        len(facts_created),
                        wiz.actions != "draft" and "Sí" or "No",
                        wiz.actions == "open-group-order-send" and "Sí" or "No",
                    ),
                ]
            )
        return msg, fact_csv_result

    def refund_rectify_by_origin(self, cursor, uid, ids, context={}):  # noqa: C901
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")

        wiz = self.browse(cursor, uid, ids[0])

        if wiz.actions == "open-group-order-send" and not (
            wiz.email_template_to_pay and wiz.email_template_to_refund
        ):
            raise osv.except_osv(_("Error"), _("Per enviar el correu cal indicar les plantilles"))
        if wiz.email_template_to_pay and not wiz.email_template_to_pay.enforce_from_account:
            raise osv.except_osv(
                _("Error"),
                _("La plantilla de pagament no té indicat el compte des del qual enviar"),
            )
        if wiz.email_template_to_refund and not wiz.email_template_to_refund.enforce_from_account:
            raise osv.except_osv(
                _("Error"),
                _("La plantilla de cobrament no té indicat el compte des del qual enviar"),
            )
        if wiz.actions in ["open-group-order-send", "open-group-order"] and not wiz.order:
            raise osv.except_osv(
                _("Error"), _("Per remesar les factures a pagar cal una ordre de pagament")
            )

        msg = []
        active_ids = context.get("active_ids", [])
        sorted_ids = f1_obj.search(
            cursor, uid, [("id", "in", active_ids)], order="fecha_factura_desde"
        )
        facts_generades = []
        facts_by_polissa = {}
        fact_csv_result = []
        f1_refacturats = []
        for _id in sorted_ids:
            f1 = f1_obj.browse(cursor, uid, _id)
            origen = f1.invoice_number_text
            pol_id = f1.polissa_id.id
            pol_name = f1.polissa_id.name
            try:
                if f1.type_factura != "R":
                    msg.append(
                        "La pòlissa {}, que té l'F1 amb origen {}, l'F1 no és tipus rectificatiu. No s'actua.".format(  # noqa: E501
                            pol_name, origen
                        )
                    )
                    fact_csv_result.append([origen, pol_name, "F1 no és tipus rectificatiu"])
                    continue

                if f1.polissa_id.facturacio_suspesa:
                    msg.append(
                        "La pòlissa {}, que té l'F1 amb origen {}, té facturació suspesa. No s'actua.".format(  # noqa: E501
                            pol_name, origen
                        )
                    )
                    fact_csv_result.append([origen, pol_name, "Pòlissa amb facturació suspesa"])
                    continue

                facts_cli_ids, msg_get = self.get_factures_client_by_dates(
                    cursor,
                    uid,
                    ids,
                    pol_id,
                    f1.fecha_factura_desde,
                    f1.fecha_factura_hasta,
                    context,
                )
                if msg_get:
                    msg.append(
                        "Pòlissa {} per l'F1 amb origen {}: {}".format(pol_name, origen, msg_get)
                    )
                if not facts_cli_ids:
                    msg.append(
                        "L'F1 amb origen {} no té res per abonar i rectificar perquè no hi ha factura generada, no s'actua".format(  # noqa: E501
                            origen
                        )
                    )
                    fact_csv_result.append(
                        [
                            origen,
                            pol_name,
                            "No té res per abonar i rectificar perquè no hi ha factura generada, no s'actua",  # noqa: E501
                        ]
                    )
                    self.add_f1_observation(
                        cursor,
                        uid,
                        _id,
                        "F1 NO refacturat en data {} per falta de factura generada".format(
                            get_today()
                        ),
                        context,
                    )
                    continue

                n_lect_del = self.recarregar_lectures_between_dates(
                    cursor,
                    uid,
                    ids,
                    pol_id,
                    f1.fecha_factura_desde,
                    f1.fecha_factura_hasta,
                    context,
                )
                if not n_lect_del:
                    msg.append(
                        "La pòlissa {}, que té l'F1 amb origen {}, no té lectures per esborrar. No s'hi actua.".format(  # noqa: E501
                            pol_name, origen
                        )
                    )
                    fact_csv_result.append(
                        [origen, pol_name, "No té lectures per esborrar. No s'hi actua."]
                    )
                    continue

                facts_created = self.refund_rectify_if_needed(cursor, uid, facts_cli_ids, context)
                msg_rr, facts_created = self.delete_draft_invoices_if_needed(
                    cursor, uid, facts_created, facts_cli_ids, context
                )
                msg.append(
                    "S'han esborrat {} lectures de la pòlissa {} i s'han generat {} factures".format(  # noqa: E501
                        n_lect_del, pol_name, len(facts_created)
                    )
                )
                facts_generades += facts_created
                msg += msg_rr
                f1_refacturats.append({"id": _id, "refund_result": msg_rr})
                if wiz.max_amount:
                    facts_over_limit = self.check_max_amount(
                        cursor, uid, ids, facts_created, wiz.max_amount, context
                    )
                    if facts_over_limit:
                        msg.append(
                            "La pòlissa {} té alguna factura d'import superior al límit, cal revisar les factures. No continua el procés.".format(  # noqa: E501
                                pol_name
                            )
                        )
                        fact_csv_result.append(
                            [
                                origen,
                                pol_name,
                                "Té alguna factura d'import superior al límit, cal revisar les factures. No continua el procés.",  # noqa: E501
                            ]
                        )
                        continue
                if facts_created and self.has_open_initial_invoices(
                    cursor, uid, ids, facts_cli_ids
                ):
                    msg.append(
                        "La pòlissa {} té alguna factura inicial oberta. No continua el procés".format(  # noqa: E501
                            pol_name
                        )
                    )
                    fact_csv_result.append(
                        [
                            origen,
                            pol_name,
                            "Té alguna factura inicial oberta, cal revisar les factures. No continua el procés.",  # noqa: E501
                        ]
                    )
                    continue
                facts_by_polissa.setdefault(pol_name, []).extend(facts_created)

            except Exception as e:
                msg.append("Error processant la factura amb origen {}: {}".format(origen, str(e)))
                fact_csv_result.append(
                    [origen, pol_name, "Hi ha hagut algun problema, cal revisar."]
                )

        if f1_refacturats and wiz.actions != "draft":
            msg_open_send, csv_open_send = self.open_polissa_invoices_send_mail(
                cursor, uid, ids, facts_by_polissa, context
            )
            msg += msg_open_send
            fact_csv_result += csv_open_send

        if f1_refacturats:
            self.save_info_into_f1_after_refacturacio(cursor, uid, f1_refacturats, context=context)

        self.write_report(cursor, uid, ids, fact_csv_result, context)
        self.write(
            cursor,
            uid,
            ids,
            {
                "info": "\n".join(msg),
                "state": "end",
                "facts_generades": json.dumps(facts_generades),
            },
        )

    def has_open_initial_invoices(self, cursor, uid, ids, facts_cli_ids):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        fact_states = fact_obj.read(cursor, uid, facts_cli_ids, ["state"])
        return "open" in [x["state"] for x in fact_states]

    def _show_invoices(self, cursor, uid, ids, context=None):
        fact_ids = self.read(cursor, uid, ids[0], ["facts_generades"])[0]["facts_generades"]
        fact_ids = json.loads(fact_ids)
        return {
            "domain": "[('id','in', %s)]" % str(fact_ids),
            "name": "Factures",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "giscedata.facturacio.factura",
            "type": "ir.actions.act_window",
        }

    _columns = {
        "state": fields.selection([("init", "Initial"), ("end", "End")], "State"),
        "order": fields.many2one("payment.order", "Remesa"),
        "actions": fields.selection(
            [
                ("draft", "Factures en esborrany"),
                ("open", "Obrir"),
                ("open-group", "Obrir i agrupar"),
                ("open-group-order", "Obrir, agrupar i remesar"),
                ("open-group-order-send", "Obrir, agrupar, remesar i enviar"),
            ],
            _("Accions:"),
        ),
        "info": fields.text(_("Informació"), readonly=True),
        "facts_generades": fields.text(),
        "max_amount": fields.float(
            "Import màxim",
            help="Import màxim a partir del qual les factures no s'obren i cal revisar. Si s'indica 0 no es comprova cap import",  # noqa: E501
        ),
        "email_template_to_pay": fields.many2one(
            "poweremail.templates",
            "Plantilla del correu a pagar",
            domain="[('object_name.model', '=', 'giscedata.polissa')]",
        ),
        "email_template_to_refund": fields.many2one(
            "poweremail.templates",
            "Plantilla del correu a cobrar",
            domain="[('object_name.model', '=', 'giscedata.polissa')]",
        ),
        "report_file": fields.binary("Resultat", help="CSV amb el resultat"),
    }

    _defaults = {
        "state": lambda *a: "init",
        "max_amount": lambda *a: 2000,
        "actions": "draft",
    }


WizardRefundRectifyFromOrigin()
