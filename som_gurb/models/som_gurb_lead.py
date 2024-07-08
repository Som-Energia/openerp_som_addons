# -*- coding: utf-8 -*-
import json
import pooler
import netsvc
import base64
from osv import osv, fields
from tools.translate import _
from tools import config
from datetime import datetime


class SomGurbLead(osv.osv):
    _name = "som.gurb.lead"
    _rec_name = "cups_id"
    _description = _("Lead de Gurb CUPS en grup de generació urbana")

    def onchange_cups_id(self, cursor, uid, ids, cups_id, context=None):
        if context is None:
            context = {}

        email = False
        pol_id = False
        pol_o = self.pool.get("giscedata.polissa")

        search_params = [
            ("state", "in", ["activa", "esborrany"]),
            ("cups", "=", cups_id),
        ]
        pol_ids = pol_o.search(cursor, uid, search_params, context=context, limit=1)

        if pol_ids:
            pol_id = pol_ids[0]
            pol_br = pol_o.browse(cursor, uid, pol_id, context=context)
            email = pol_br.direccio_notificacio.email

            write_vals = {"email": email, "polissa_id": pol_id}

            self.write(cursor, uid, context['active_id'], write_vals, context=context)

        return {
            "value": {"email": email, "polissa_id": pol_id},
            "domain": {},
            "warning": {},
        }

    def get_polissa_gurb_cups(self, cursor, uid, grub_lead_id, context=None):
        if context is None:
            context = {}

        pol_o = self.pool.get("giscedata.polissa")

        gurb_vals = self.read(cursor, uid, grub_lead_id, ["cups_id", "gurb_id", "owner_cups"])

        search_params = [
            ("state", "=", "activa"),
            ("cups", "=", gurb_vals["cups_id"][0]),
        ]
        pol_ids = pol_o.search(cursor, uid, search_params, context=context, limit=1)

        return pol_ids[0] if pol_ids else False

    def get_titular_gurb_cups(self, cursor, uid, grub_lead_id, context=None):
        if context is None:
            context = {}
        pol_o = self.pool.get("giscedata.polissa")
        pol_id = self.get_polissa_gurb_cups(cursor, uid, grub_lead_id, context=context)
        if not pol_id:
            return False
        partner_id = pol_o.read(cursor, uid, pol_id, ['titular'], context=context)
        if partner_id:
            partner_id = partner_id["titular"][0]
        return partner_id

    def create_initial_invoice(self, cursor, uid, grub_lead_id, context=None):
        if context is None:
            context = {}

        imd_o = self.pool.get("ir.model.data")
        invoice_o = self.pool.get("account.invoice")
        account_o = self.pool.get("account.account")
        journal_o = self.pool.get("account.journal")
        payment_type_o = self.pool.get("payment.type")
        invoice_line_o = self.pool.get("account.invoice.line")
        product_o = self.pool.get("product.product")
        pricelist_o = self.pool.get("product.pricelist")

        gurb_cups_br = self.browse(cursor, uid, grub_lead_id, context=context)

        if gurb_cups_br.initial_invoice_id:
            error = "[GURB CUPS ID {}]: La factura d'inscripció ja existeix.".format(
                gurb_cups_br.id,
            )
            return (False, error)

        partner_id = self.get_titular_gurb_cups(
            cursor, uid, gurb_cups_br.id, context=context
        )

        if not partner_id:
            error = "[GURB CUPS ID {}]: Error al buscar el titular de la pòlissa associada.".format(
                gurb_cups_br.id,
            )
            return (False, error)

        # Initial quota base gurb
        product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "initial_quota_gurb"
        )[1]
        product_br = product_o.browse(cursor, uid, product_id, context=context)

        # Get product price_unit from GURB pricelist
        price_unit = pricelist_o.price_get(
            cursor,
            uid,
            [gurb_cups_br.gurb_id.pricelist_id.id],
            product_id,
            gurb_cups_br.beta_kw,
        )[gurb_cups_br.gurb_id.pricelist_id.id]

        # Create invoice line
        gurb_line = invoice_line_o.product_id_change(  # Get line default values
            cursor,
            uid,
            [],
            product=product_br.id,
            uom=product_br.uom_id.id,
            partner_id=partner_id,
            type="out_invoice",
        ).get("value", {})
        gurb_line["invoice_line_tax_id"] = [(6, 0, gurb_line.get("invoice_line_tax_id", []))]
        gurb_line.update({
            "name": "Quota inicial Gurb",
            "product_id": product_id,
            "price_unit": price_unit,
            "quantity": gurb_cups_br.beta_kw,
        })

        # Create invoice
        invoice_account_ids = account_o.search(
            cursor, uid, [("code", "=", "430000000000")], context=context
        )
        journal_ids = journal_o.search(
            cursor, uid, [("code", "=", "VENTA")], context=context
        )
        payment_type_id = payment_type_o.search(
            cursor, uid, [("code", "=", "TRANSFERENCIA_CSB")], context=context
        )[0]
        invoice_lines = [
            (0, 0, gurb_line)
        ]
        invoice_vals = {
            "partner_id": partner_id,
            "type": "out_invoice",
            "invoice_line": invoice_lines,
            "origin": "GURBCUPSID{}".format(gurb_cups_br.id),
        }
        invoice_vals.update(invoice_o.onchange_partner_id(  # Get invoice default values
            cursor, uid, [], "out_invoice", partner_id).get("value", {})
        )
        invoice_vals.update({"payment_type": payment_type_id})

        if invoice_account_ids:
            invoice_vals.update({"account_id": invoice_account_ids[0]})
        if journal_ids:
            invoice_vals.update({"journal_id": journal_ids[0]})

        invoice_id = invoice_o.create(cursor, uid, invoice_vals, context=context)
        invoice_o.button_reset_taxes(cursor, uid, [invoice_id])

        # Update reference
        write_vals = {
            "initial_invoice_id": invoice_id,
        }
        self.write(cursor, uid, gurb_cups_br.id, write_vals, context=context)

        return (invoice_id, False)

    def sign_and_create_som_grub_cups(self, cursor, uid, grub_lead_ids, context=None):
        if context is None:
            context = {}
        if not isinstance(grub_lead_ids, list):
            grub_lead_ids = [grub_lead_ids]

        errors = []
        invoice_ids = []

        for grub_lead_id in grub_lead_ids:
            try:
                invoice_id, error = self.create_initial_invoice(
                    cursor, uid, grub_lead_id, context=context
                )
                if error:
                    errors.append(error)
                else:
                    invoice_ids.append(invoice_id)
            except Exception as e:
                errors.append(
                    "[GURB CUPS ID {}]: {}".format(
                        grub_lead_id,
                        e.message,
                    )
                )

        return (invoice_ids, errors)

    def create_gurb_cups(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        gurb_cups_o = self.pool.get("som.gurb.cups")

        for lead_id in ids:
            # TODO create BETA
            lead = self.browse(cursor, uid, lead_id, context=context)
            create_vals = {
                "active": True,
                "start_date": datetime.today().strftime("%Y-%m-%d"),
                "gurb_id": lead.gurb_id.id,
                "cups_id": lead.cups_id.id,
                "general_conditions_id": lead.general_conditions_id.id,
            }
            gurb_cups_id = gurb_cups_o.create(cursor, uid, create_vals, context=context)
            self.write(cursor, uid, lead_id, {'gurb_cups_id': gurb_cups_id}, context=context)

    def consentiment_baixa_pdf(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        return self.document_pdf(
            cursor, uid, ids, 'report.report_som_gurb_consentiment_baixa', context=context
        )

    def condicions_pdf(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        return self.document_pdf(
            cursor, uid, ids, 'report.som.gurb.conditions', context=context
        )

    def representant_pdf(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        return self.document_pdf(
            cursor, uid, ids, 'report.report_som_gurb_autoritzacio_representant', context=context
        )

    def document_pdf(self, cursor, uid, ids, report_name, context=None):
        # el cursor que ens cau esta en readonly pq aixi ho posa la funció
        # d'imprimir reports → hem de fer servir un de nou per poder crear
        # el contracte
        cr = pooler.get_db(cursor.dbname).cursor()

        if context is None:
            context = {}
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        ctx = context.copy()
        ctx['prefetch'] = False

        report = netsvc.LocalService(report_name)

        lead = self.browse(cr, uid, ids[0], context=ctx)

        savepoint = 'savepoint_gurb_consentiment_{}'.format(id(cr))
        cr.savepoint(savepoint)
        try:
            # lead.force_validation()
            if not lead.gurb_cups_id:
                self.create_gurb_cups(cr, uid, ids, context=context)
            lead = self.browse(cr, uid, ids[0], context=ctx)
            result, result_format = report.create(
                cr, uid, [lead.gurb_cups_id.id], {}, context=context
            )
            cr.rollback(savepoint)
            cr.commit()
            return {
                'content': base64.b64encode(result),
                'format': result_format
            }
        except Exception as e:
            print(e)
            cr.rollback()
            raise
        finally:
            cr.close()

    def get_document_action_report(self, cursor, uid, action_report, context=None):
        """
        Get the object reference of a action report semantic id
        :param cursor: db cursor
        :param uid: erp user id
        :param action_report: Semantic id
        :param context:
        :return: action report id
        """
        if context is None:
            context = {}
        imd_obj = self.pool.get("ir.model.data")
        report_id = imd_obj.get_object_reference(cursor, uid, "som_gurb", action_report)[1]
        return report_id

    def sign_gurb_lead(self, cursor, uid, ids, context=None):
        """
        Starts a signature process for the 3 gurb documents :)
        :param cursor: db cursor
        :param uid: erp user id
        :param gurb_cups_id: The Gurb Cups id signed
        :param context:
        :return: giscedata.sigantura.process created id
        """
        if context is None:
            context = {}

        imd_obj = self.pool.get("ir.model.data")
        attach_obj = self.pool.get("ir.attachment")
        pro_obj = self.pool.get("giscedata.signatura.process")

        process_ids = []
        for gurb_lead_id in ids:
            gurb_lead_br = self.browse(cursor, uid, gurb_lead_id, context=context)
            if not gurb_lead_id:
                raise osv.except_osv(
                    "Registre actiu", "Aquest assistent necessita un registre actiu!")

            branding_id = config.get("signaturit_branding_id") or ""

            autoritzacio_id = self.get_document_action_report(
                cursor, uid,
                "action_report_som_gurb_lead_autoritzacio_representant", context=context
            )
            baixa_id = self.get_document_action_report(
                cursor, uid, "action_report_som_gurb_lead_consentiment_baixa", context=context
            )
            condicions_id = self.get_document_action_report(
                cursor, uid, "action_report_som_gurb_lead_conditions", context=context
            )

            process_data = context.get("process_data", {}).copy()
            data = json.dumps(process_data)
            doc_categ_id = attach_obj.get_category_for(
                cursor, uid, "gurb", context=context)

            process_files = [
                (0, 0, {
                    "model": "som.gurb.lead,{}".format(gurb_lead_id),
                    "report_id": autoritzacio_id,
                    "category_id": doc_categ_id
                }),
                (0, 0, {
                    "model": "som.gurb.lead,{}".format(gurb_lead_id),
                    "report_id": baixa_id,
                    "category_id": doc_categ_id
                }),
                (0, 0, {
                    "model": "som.gurb.lead,{}".format(gurb_lead_id),
                    "report_id": condicions_id,
                    "category_id": doc_categ_id
                }),
            ]

            email = gurb_lead_br.email

            tmpl_id = imd_obj.get_object_reference(
                cursor, uid, "som_gurb", "email_signature_process_gurb_lead"
            )[1]
            cc = pro_obj.get_cc_signature(
                cursor, uid, [gurb_lead_id], "gurb", context=context
            )
            expire_time = pro_obj.get_expire_time_signature(
                cursor, uid, [gurb_lead_id], "gurb", context=context
            )

            reminders = pro_obj.get_reminder(
                cursor, uid, [gurb_lead_id], "gurb", context=context
            )

            partner_address = ""
            name = ""

            values = {
                "template_id": tmpl_id,
                "template_res_id": gurb_lead_id,
                "delivery_type": context.get("delivery_type", "poweremail"),
                "branding_id": branding_id,
                "recipients": [
                    (0, 0, {
                        "partner_address_id": partner_address,
                        "name": name,
                        "email": email,
                    })
                ],
                "lang": 'ca_ES',  # TODO
                "reminders": reminders,
                "data": data,
                "all_signed": True,
                "files": process_files,
                "cc": cc,
                "provider": "signaturit"
            }

            if expire_time:
                values["expire_time"] = expire_time

            process_id = pro_obj.create(cursor, uid, values, context)
            process_ids = process_id
            self.write(cursor, uid, gurb_lead_id, {'signature_id': process_id})

            # Executar l'inici del proces
            pro_obj.start(cursor, uid, [process_id], context=None)

        res = {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'giscedata.signatura.process',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [process_ids])]
        }
        return res

    _columns = {
        "active": fields.boolean("Actiu"),
        "signed": fields.boolean("Firmat", readonly=True),
        "payed": fields.boolean("Pagat", readonly=True),
        "gurb_id": fields.many2one("som.gurb", "GURB", required=True, ondelete="cascade"),
        "gurb_cups_id": fields.many2one("som.gurb.cups", "GURB cups", required=False),
        "cups_id": fields.many2one("giscedata.cups.ps", "CUPS", required=True),
        "beta_inicial": fields.float("Beta inicial (kWh)", digits=(16, 6)),
        "extra_beta_inicial": fields.float("Extra Beta inicial (kWh)", digits=(16, 6)),
        "email": fields.char("Email a signar", required=True, size=320),
        "general_conditions_id": fields.many2one(
            "som.gurb.general.conditions",
            "Condicions generals",
            required=False,
        ),
        "initial_invoice_id": fields.many2one("account.invoice", "Factura"),
        "polissa_id": fields.many2one("giscedata.polissa", "Pòlissa", readonly=True),
        "signature_id": fields.many2one(
            "giscedata.signatura.process", "Proces de Firma vinculat", readonly=True),
        "partner_id": fields.related(
            "polissa_id",
            "titular",
            type="many2one",
            relation="res.partner",
            string="Client",
            store=False,
            readonly=True,
        ),
    }

    _defaults = {
        "active": lambda *a: True,
    }


SomGurbLead()
