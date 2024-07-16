# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
from osv import osv, fields
from tools import config


class WizardGurbCreateGurbCupsSignature(osv.osv_memory):
    _name = "wizard.create.gurb.cups.signature"
    _description = "Wizard per crear la Signatura d'un Gurb Cups"

    def _default_email(self, cursor, uid, context=None):
        if context is None:
            context = {}

        email = False

        gurb_cups_id = context.get('active_id')
        gurb_cups_obj = self.pool.get('som.gurb.cups')
        gurb_cups = gurb_cups_obj.browse(cursor, uid, gurb_cups_id, context=context)
        if gurb_cups.polissa_id:
            email = gurb_cups.polissa_id.direccio_pagament.email
        return email

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

    def validate_gurb_cups(self, cursor, uid, gurb_cups_id, context=None):
        if context is None:
            context = {}

        gurb_cups = self.browse(cursor, uid, gurb_cups_id, context=context)

        if not gurb_cups.general_conditions_id or len(gurb_cups.betas_ids) <= 0:
            osv.except_osv("Betes i condicons", "Falten les condicions del gurb i/o les betes")

    def start_signature_process(self, cursor, uid, ids, context=None):
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
        partner_obj = self.pool.get("res.partner")
        attach_obj = self.pool.get("ir.attachment")
        grub_cups_obj = self.pool.get("som.gurb.cups")
        pro_obj = self.pool.get("giscedata.signatura.process")

        wiz = self.browse(cursor, uid, ids[0], context=context)
        gurb_cups_id = context.get("active_id", False)

        self.validate_gurb_cups(cursor, uid, gurb_cups_id, context=context)

        if not gurb_cups_id:
            raise osv.except_osv("Registre actiu", "Aquest assistent necessita un registre actiu!")

        branding_id = config.get("signaturit_branding_id") or ""

        titular_id = grub_cups_obj.get_titular_gurb_cups(cursor, uid, gurb_cups_id, context=context)
        titular = partner_obj.browse(cursor, uid, titular_id, context=context)

        autoritzacio_id = self.get_document_action_report(
            cursor, uid, "action_report_som_gurb_autoritzacio_representant", context=context
        )
        baixa_id = self.get_document_action_report(
            cursor, uid, "action_report_som_gurb_consentiment_baixa", context=context
        )
        condicions_id = self.get_document_action_report(
            cursor, uid, "action_report_som_gurb_conditions", context=context
        )

        process_data = context.get("process_data", {}).copy()
        data = json.dumps(process_data)
        doc_categ_id = attach_obj.get_category_for(
            cursor, uid, "gurb", context=context)

        process_files = [
            (0, 0, {
                "model": "som.gurb.cups,{}".format(gurb_cups_id),
                "report_id": autoritzacio_id,
                "category_id": doc_categ_id
            }),
            (0, 0, {
                "model": "som.gurb.cups,{}".format(gurb_cups_id),
                "report_id": baixa_id,
                "category_id": doc_categ_id
            }),
            (0, 0, {
                "model": "som.gurb.cups,{}".format(gurb_cups_id),
                "report_id": condicions_id,
                "category_id": doc_categ_id
            }),
        ]

        email = wiz.email

        tmpl_id = imd_obj.get_object_reference(
            cursor, uid, "som_gurb", "email_signature_process_gurb"
        )[1]
        cc = pro_obj.get_cc_signature(
            cursor, uid, [gurb_cups_id], "gurb", context=context
        )
        expire_time = pro_obj.get_expire_time_signature(
            cursor, uid, [gurb_cups_id], "gurb", context=context
        )

        lang = titular.lang

        reminders = pro_obj.get_reminder(
            cursor, uid, [gurb_cups_id], "gurb", context=context
        )

        partner_address = ""
        name = ""

        values = {
            "template_id": tmpl_id,
            "template_res_id": gurb_cups_id,
            "delivery_type": context.get("delivery_type", "poweremail"),
            "branding_id": branding_id,
            "recipients": [
                (0, 0, {
                    "partner_address_id": partner_address,
                    "name": name,
                    "email": email,
                })
            ],
            "lang": lang,
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

        # Executar l'inici del proces
        pro_obj.start(cursor, uid, [process_id], context=None)
        res = {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'giscedata.signatura.process',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [process_id])]
        }
        return res

    _columns = {
        "email": fields.char("Email", size=320, required=True),
    }

    _defaults = {
        "email": _default_email
    }


WizardGurbCreateGurbCupsSignature()
