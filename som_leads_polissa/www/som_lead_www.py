# -*- encoding: utf-8 -*-
from __future__ import absolute_import, division

import logging
import traceback
import sys
import time
from osv import osv
from service.security import Sudo
from oorq.decorators import job
import yaml
import copy
import pooler
from uuid import uuid4
from psycopg2.errors import LockNotAvailable

from som_leads_polissa.models.giscedata_crm_lead import WWW_DATA_FORM_HEADER
from giscedata_cups.giscedata_cups import get_dso
from tools.sql_utils import auto_close_cursor


class SomLeadWww(osv.osv_memory):
    _name = "som.lead.www"

    _CONTRACT_TYPE_ANUAL = '01'
    _FACTURACIO_MENSUAL = 1
    _127_WITH_SURPLUSES = '2'
    _128_SIMPLIFIED_SURPLUSES = 'a0'
    _131_CONSUMPTION = '01'
    _SIGNATURE_COMPLETED_STATUS = 'completed'
    _SIGNATURE_ERROR_STATUSES = ('error', 'canceled', 'declined', 'expired')

    def create_lead(self, cr, uid, www_vals, context=None):
        if context is None:
            context = {}
        lead_o = self.pool.get("giscedata.crm.lead")
        ir_model_o = self.pool.get("ir.model.data")

        payment_data = self._resolve_payment_configuration(cr, uid, www_vals, context=context)
        contract_data = self._resolve_contract_data(cr, uid, www_vals, context=context)
        member_type, member = self._resolve_member_data(cr, uid, www_vals, context=context)
        member = self._normalize_member_data(cr, uid, member, context=context)

        values = self._build_lead_values(
            cr, uid, www_vals, member_type, member, contract_data, payment_data, context=context
        )
        values = self._apply_self_consumption_values(cr, uid, values, www_vals, context=context)
        values = self._finalize_lead_values(values)

        lead_id = lead_o.create(cr, uid, values, context=context)
        self._create_attachments(cr, uid, lead_id, www_vals.get("attachments", []), context=context)
        self._save_www_data_in_history(cr, uid, lead_id, www_vals, context=context)
        lead_o.copy_base_attr_gen_from_titular(cr, uid, lead_id)
        lead_o.assign_contract_number(cr, uid, lead_id, context=context)

        # similar to lead.contract_pdf but simpler (contract_pdf fails because the 2nd cursor)
        error_info = self._check_lead_can_be_activated(cr, uid, lead_id, context=context)

        if error_info:
            # Set the stage to error and state to pending
            error_stage_id = ir_model_o.get_object_reference(
                cr, uid, "som_leads_polissa", "webform_stage_error"
            )[1]
            lead_o.write(
                cr, uid, lead_id,
                {'stage_id': error_stage_id, 'state': 'pending'},
                context=context
            )

        return {
            "lead_id": lead_id,
            "error": error_info,
        }

    def _resolve_payment_configuration(self, cr, uid, www_vals, context=None):
        if context is None:
            context = {}

        payment_mode_o = self.pool.get("payment.mode")
        ir_model_o = self.pool.get("ir.model.data")

        payment_type = www_vals.get("payment_type")
        billing_payment_method = www_vals.get("billing_payment_method")

        if not billing_payment_method:
            billing_payment_method = (
                "card_recurrent" if payment_type == "tpv" else "remesa"
            )

        valid_payment_configuration = (
            (payment_type == "tpv" and billing_payment_method == "card_recurrent")
            or (payment_type == "remesa" and billing_payment_method == "remesa")
        )
        if not valid_payment_configuration:
            raise osv.except_osv(
                "INVALID_PAYMENT_CONFIGURATION",
                "La forma de pagament de la quota i la de la facturacio han de ser coherents."
            )

        if billing_payment_method == 'card_recurrent':
            payment_mode_id = ir_model_o.get_object_reference(
                cr, uid, "som_card_payment", "payment_mode_card_recurrent"
            )[1]
        else:
            enginyers_ids = payment_mode_o.search(cr, uid, [("name", "=", "ENGINYERS")], limit=1)
            if not enginyers_ids:
                raise osv.except_osv(
                    "MISSING_PAYMENT_MODE",
                    "No s'ha trobat el mode de pagament 'ENGINYERS'."
                )
            payment_mode_id = enginyers_ids[0]

        return {
            "payment_type": payment_type,
            "billing_payment_method": billing_payment_method,
            "payment_mode_id": payment_mode_id,
        }

    def _resolve_contract_data(self, cr, uid, www_vals, context=None):
        if context is None:
            context = {}

        imd_o = self.pool.get("ir.model.data")
        polissa_o = self.pool.get("giscedata.polissa")
        tarifa_o = self.pool.get("giscedata.polissa.tarifa")
        cnae_o = self.pool.get("giscemisc.cnae")

        contract_info = www_vals["contract_info"]
        contract_address = contract_info["cups_address"]

        tensio_xml_id = 'tensio_230'
        if contract_info.get("phase") == "3x230/400":
            tensio_xml_id = 'tensio_3x230_400'
        tensio_id = imd_o.get_object_reference(cr, uid, 'giscedata_tensions', tensio_xml_id)[1]

        tarifa_id = tarifa_o.search(cr, uid, [("name", "=", contract_info["tariff"])])[0]
        tariff_mode = 'index' if contract_info["is_indexed"] else 'atr'
        llista_preu_id = polissa_o.get_pricelist_from_tariff_and_location(
            cr, uid, contract_info["tariff"], tariff_mode, contract_address["city_id"], context
        ).id

        try:
            cnae_id = cnae_o.search(cr, uid, [("name", "=", contract_info["cnae"])])[0]
        except IndexError:
            cnae_id = None

        return {
            "contract_info": contract_info,
            "contract_address": contract_address,
            "tensio_id": tensio_id,
            "tarifa_id": tarifa_id,
            "llista_preu_id": llista_preu_id,
            "cnae_id": cnae_id,
            "distri_ref": get_dso(contract_info["cups"]),
        }

    def _resolve_member_data(self, cr, uid, www_vals, context=None):
        if context is None:
            context = {}

        member_type = www_vals["linked_member"]
        if member_type == "new_member":
            self._check_member_vat_dont_exists(
                cr, uid, www_vals["new_member_info"]["vat"], context=context
            )
            return member_type, www_vals["new_member_info"]

        if member_type in ["sponsored", "already_member"]:
            self._check_member_vat_number_matching(
                cr, uid, www_vals["linked_member_info"]["vat"],
                www_vals["linked_member_info"]["code"], context=context
            )
            if member_type == "sponsored":
                member = www_vals["contract_owner"]
                context["sponsored_titular"] = True
            else:
                member = {
                    "vat": www_vals["linked_member_info"]["vat"],
                    "address": {},
                }
            member["number"] = "S" + www_vals["linked_member_info"]["code"].zfill(6)
            return member_type, member

        raise osv.except_osv(
            "Error",
            "linked_member value not valid: %s" % member_type
        )

    def _normalize_member_data(self, cr, uid, member, context=None):
        if context is None:
            context = {}

        partner_o = self.pool.get("res.partner")

        member["phone_prefix"], member["phone"] = self._split_phone_prefix(
            cr, uid, member.get("phone")
        )
        member["mobile_prefix"], member["phone2"] = self._split_phone_prefix(
            cr, uid, member.get("phone2")
        )

        if member.get("name") and member.get("surname"):
            names = partner_o.separa_cognoms(
                cr, uid, "{}, {}".format(member["surname"], member["name"])
            )
            member.update({
                'name': names['nom'],
                'surname': names['cognoms'][0],
                'surname2': names['cognoms'][1],
            })

        return member

    def _build_lead_values(
        self, cr, uid, www_vals, member_type, member, contract_data, payment_data, context=None
    ):
        if context is None:
            context = {}

        ir_model_o = self.pool.get("ir.model.data")
        member_o = self.pool.get("somenergia.soci")
        contract_info = contract_data["contract_info"]
        contract_address = contract_data["contract_address"]

        values = {
            "state": "open",
            "name": "{} / {}".format(member["vat"].upper(), contract_info["cups"]),
            "cups": contract_info["cups"],
            "codigoEmpresaDistribuidora": contract_data["distri_ref"],
            "cups_ref_catastral": contract_info.get("cups_cadastral_reference"),
            "cups_zip": contract_address["postal_code"],
            "cups_id_municipi": contract_address["city_id"],
            "cups_nv": contract_address["street"],
            "cups_pnp": contract_address.get("number"),
            "cups_pt": contract_address.get("floor"),
            "cups_es": contract_address.get("stair"),
            "cups_pu": contract_address.get("door"),
            "cups_bq": contract_address.get("block"),
            "cnae": contract_data["cnae_id"],
            "tarifa": contract_data["tarifa_id"],
            "facturacio_potencia": 'max' if contract_info["tariff"] == '3.0TD' else 'icp',
            "tensio_normalitzada": contract_data["tensio_id"],
            "atr_proces_name": contract_info['process'],
            "change_adm": contract_info['process'] == 'C2',
            "contract_type": self._CONTRACT_TYPE_ANUAL,
            "llista_preu": contract_data["llista_preu_id"],
            "facturacio": self._FACTURACIO_MENSUAL,
            "iban": www_vals.get("iban"),
            "payment_mode_id": payment_data["payment_mode_id"],
            "enviament": "email",
            "create_new_member": member_type == "new_member",
            "autoconsumo": "00",
            "member_number": member.get("number"),
            "titular_vat": 'ES%s' % member["vat"].upper(),
            "titular_nom": member.get("name"),
            "titular_cognom1": member.get("surname"),
            "titular_cognom2": member.get("surname2"),
            "tipus_vivenda": 'habitual',
            "titular_zip": member["address"].get("postal_code"),
            "titular_nv": member["address"].get("street"),
            "titular_pnp": member["address"].get("number"),
            "titular_pt": member["address"].get("floor"),
            "titular_es": member["address"].get("stair"),
            "titular_pu": member["address"].get("door"),
            "titular_bq": member["address"].get("block"),
            "titular_id_municipi": member["address"].get("city_id"),
            "titular_email": member.get("email", "").lower() or None,
            "titular_phone": member.get("phone"),
            "titular_mobile": member.get("phone2"),
            "titular_phone_prefix": member.get("phone_prefix"),
            "titular_mobile_prefix": member.get("mobile_prefix"),
            "use_cont_address": False,
            "donation": www_vals.get("donation", False),
            "member_quota_payment_type": payment_data["payment_type"],
            "billing_payment_method": payment_data["billing_payment_method"],
            "gender": member.get("gender"),
            "birthdate": member.get("birthdate"),
            "referral_source": member.get("referral_source"),
            "comercial_info_accepted": member.get("comercial_info_accepted", False),
            "mandate_number": uuid4().hex,
        }

        values["user_id"] = ir_model_o.get_object_reference(
            cr, uid, "base_extended_som", "res_users_webforms"
        )[1]
        values["stage_id"] = ir_model_o.get_object_reference(
            cr, uid, "som_leads_polissa", "webform_stage_recieved"
        )[1]
        values["section_id"] = ir_model_o.get_object_reference(
            cr, uid, "som_leads_polissa", "webform_section"
        )[1]

        if member.get("is_juridic"):
            values["persona_firmant_vat"] = member["proxy_vat"]
            values["persona_nom"] = member["proxy_name"]
            values["is_juridic"] = True

        for i, power in enumerate(contract_info["powers"]):
            values["potenciasContratadasEnKWP%s" % str(i + 1)] = float(power) / 1000

        if member.get("lang", False):
            values["lang"] = member["lang"]
        else:
            if member_type in ["sponsored", "already_member"]:
                member_id = self._check_member_vat_number_matching(
                    cr, uid, www_vals["linked_member_info"]["vat"],
                    www_vals["linked_member_info"]["code"], context=context
                )
                if member_id:
                    member_br = member_o.browse(cr, uid, member_id, context=context)
                    if member_br.partner_id.lang and values.get("lang") is None:
                        values["lang"] = member_br.partner_id.lang

        values["is_new_contact"] = (
            not self._already_has_contract(cr, uid, values["titular_vat"], context=context)
        )

        return values

    def _apply_self_consumption_values(self, cr, uid, values, www_vals, context=None):
        if context is None:
            context = {}

        if not www_vals.get("self_consumption"):
            return values

        selfcons_o = self.pool.get("giscedata.autoconsum")
        values["seccio_registre"] = self._127_WITH_SURPLUSES
        values["subseccio"] = self._128_SIMPLIFIED_SURPLUSES
        values["tipus_cups"] = self._131_CONSUMPTION
        values["cau"] = www_vals["self_consumption"]["cau"]
        values["collectiu"] = www_vals["self_consumption"]["collective_installation"]
        values["tec_generador"] = www_vals["self_consumption"]["technology"]
        values["pot_instalada_gen"] = float(
            www_vals["self_consumption"]["installation_power"]
        ) / 1000
        values["tipus_installacio"] = www_vals["self_consumption"]["installation_type"]
        values["ssaa"] = 'S' if www_vals["self_consumption"]['aux_services'] else 'N'
        values["autoconsumo"] = selfcons_o.get_ree_autoconsum_type_from_attrs(
            values["seccio_registre"], values["subseccio"], int(values["collectiu"]),
            int(values["tipus_cups"]), int(values["tipus_installacio"]), context=context
        )
        return values

    def _finalize_lead_values(self, values):
        for field, value in values.items():
            if value is None:
                del values[field]
        values["titular_id_poblacio"] = None
        return values

    def _payment_allows_activation(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get("giscedata.crm.lead")
        lead = lead_o.browse(cr, uid, lead_id, context=context)

        result = True

        if lead.billing_payment_method == "card_recurrent" and not lead.creditcard_token:
            result = False
        return result

    def add_payment_card_data(self, cr, uid, lead_id, card_vals, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get("giscedata.crm.lead")
        ir_model_o = self.pool.get("ir.model.data")
        lead = lead_o.browse(cr, uid, lead_id, context=context)

        if lead.billing_payment_method != "card_recurrent":
            raise osv.except_osv(
                "INVALID_PAYMENT_METHOD",
                "El lead no te configurat el pagament per targeta recurrent."
            )

        if lead.polissa_id:
            raise osv.except_osv(
                "LEAD_ALREADY_ACTIVATED",
                "No es poden afegir dades de targeta a un lead ja activat."
            )

        if lead.creditcard_token:
            raise osv.except_osv(
                "CARD_ALREADY_DEFINED",
                "Aquest lead ja te dades de targeta informades."
            )

        required_fields = ["creditcard_token", "creditcard_masked_number",
                           "creditcard_expiry_date", "creditcard_cof_txnid"]
        missing_fields = [field for field in required_fields if not card_vals.get(field)]
        if missing_fields:
            raise osv.except_osv(
                "INVALID_CARD_DATA",
                "Falten dades obligatories de la targeta: {}".format(", ".join(missing_fields))
            )

        payment_mode_id = ir_model_o.get_object_reference(
            cr, uid, "som_card_payment", "payment_mode_card_recurrent"
        )[1]

        lead_o.write(
            cr,
            uid,
            lead_id,
            {
                "payment_mode_id": payment_mode_id,
                "creditcard_token": card_vals["creditcard_token"],
                "creditcard_masked_number": card_vals["creditcard_masked_number"],
                "creditcard_expiry_date": card_vals["creditcard_expiry_date"],
                "creditcard_cof_txnid": card_vals["creditcard_cof_txnid"],
            },
            context=context,
        )

        error_info = self._check_lead_can_be_activated(cr, uid, lead_id, context=context)
        if error_info:
            error_stage_id = ir_model_o.get_object_reference(
                cr, uid, "som_leads_polissa", "webform_stage_error"
            )[1]
            lead_o.write(
                cr,
                uid,
                lead_id,
                {"stage_id": error_stage_id, "state": "pending"},
                context=context,
            )
        else:
            received_stage_id = ir_model_o.get_object_reference(
                cr, uid, "som_leads_polissa", "webform_stage_recieved"
            )[1]
            lead_o.write(
                cr,
                uid,
                lead_id,
                {"stage_id": received_stage_id, "state": "open"},
                context=context,
            )

        return {
            "lead_id": lead_id,
            "error": error_info,
        }

    def _signature_allows_activation(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get("giscedata.crm.lead")
        ir_model_o = self.pool.get("ir.model.data")
        sign_process_obj = self.pool.get("giscedata.signatura.process")
        logger = logging.getLogger("openerp.{0}.activate_lead.signature_mail".format(__name__))

        attempts = 30
        wait_seconds = 10

        for _ in range(attempts):
            lead_data = lead_o.read(
                cr, uid, lead_id, ['signature_process', 'status_firma'], context=context
            )
            signature_process = lead_data.get('signature_process')
            signature_status = lead_data.get('status_firma')

            if not signature_process:
                return True

            if signature_status == self._SIGNATURE_COMPLETED_STATUS:
                return True

            if signature_status in self._SIGNATURE_ERROR_STATUSES:
                return False

            sign_process_obj.update(cr, uid, [signature_process[0]], context=context)
            time.sleep(wait_seconds)

        logger.warning(
            "Signature still pending, activation e-mail not sent yet (lead_id=%s)", lead_id
        )
        signature_pending_review_stage_id = ir_model_o.get_object_reference(
            cr, uid, "som_leads_polissa", "webform_stage_signature_pending_review"
        )[1]
        lead_o.write(
            cr, uid, lead_id,
            {'stage_id': signature_pending_review_stage_id, 'state': 'pending'},
            context=context
        )
        lead_o.historize_msg(
            cr, uid, [lead_id],
            u"SIGNATURE_PENDING: activation e-mail not sent yet",
            context=context
        )
        cr.commit()
        return False

    def activate_lead(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}
        self.activate_lead_async(cr, uid, lead_id, context=context)
        return True

    @auto_close_cursor()
    def retry_lead_activation_cron(self, cr, uid, ids, context=None):
        # cursor is never used and cause idle in transaction
        if context is None:
            context = {}
        dbname = cr.dbname
        db = pooler.get_db(dbname)

        tmp_cursor = db.cursor()
        try:
            query = """SELECT l.id from giscedata_crm_lead as l
                       LEFT JOIN crm_case as c on c.id = l.crm_id
                       where c.state in ('open', 'pending')
                       and l.create_date >= now() - INTERVAL '7 days'
                       order by id desc
                       FOR UPDATE skip locked
                       """
            tmp_cursor.execute(query)
            all_data = tmp_cursor.fetchall()
            all_ids = [x[0] for x in all_data]
        except LockNotAvailable:
            return False
        finally:
            tmp_cursor.close()
        for lead_id in all_ids:
            self.activate_lead_async(cr, uid, lead_id, context=context)

    @job(queue="leads")
    def activate_lead_async(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}
        self.activate_lead_sync(cr, uid, lead_id, context=context)

    def activate_lead_sync(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get("giscedata.crm.lead")
        soci_obj = self.pool.get("somenergia.soci")
        rpa_o = self.pool.get("res.partner.address")
        ir_model_o = self.pool.get("ir.model.data")

        signature_allows = self._signature_allows_activation(cr, uid, lead_id, context=context)
        payment_allows = self._payment_allows_activation(cr, uid, lead_id, context=context)

        logger = logging.getLogger("openerp.{0}.activate_lead".format(__name__))

        if signature_allows and payment_allows:
            context["create_draft_atr"] = True
            msg = lead_o.create_entities(cr, uid, lead_id, context=context)

            lead_o.historize_msg(cr, uid, [lead_id], msg, context=context)
            lead_o.stage_next(cr, uid, [lead_id], context=context)

            try:
                # Si no és sòcia, subscriu mail a mailchimp com a client sense ser soci
                partner = lead_o.browse(cr, uid, lead_id).partner_id
                if not soci_obj.search(cr, uid, [("partner_id", "=", partner.id)]):
                    rpa_o.subscribe_partner_in_customers_no_members_lists(
                        cr, uid, partner.id, context=context)
            except Exception as e:
                sentry = self.pool.get('sentry.setup')
                if sentry:
                    sentry.client.captureException()
                logger.warning("Error al comunicar amb Mailchimp {}".format(str(e)))

            if context.get("sync"):
                self._send_activation_mail_sync(cr, uid, lead_id, context=context)
            else:
                self._send_activation_mail_async(cr, uid, lead_id, context=context)

            return True
        else:
            logger.warning("Webform stage error (lead_id=%s)", lead_id)

            signature_pending_review_stage_id = ir_model_o.get_object_reference(
                cr, uid, "som_leads_polissa", "webform_stage_error"
            )[1]
            lead_o.write(
                cr, uid, lead_id,
                {'stage_id': signature_pending_review_stage_id, 'state': 'pending'},
                context=context
            )
            msg = u"ERROR: No s'ha pogut activar aquest lead." \
                u"És probable que la signatura o el pagament no estiguin completats."

            lead_o.historize_msg(cr, uid, [lead_id], msg, context=context)
            return False

    @job(queue="poweremail_sender")
    def _send_activation_mail_async(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}
        self._send_activation_mail_sync(cr, uid, lead_id, context=context)

    def _send_activation_mail_sync(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get("giscedata.crm.lead")

        lead_o._send_mail(cr, uid, lead_id, context=context)

        cr.commit()
        return True

    def _create_attachments(self, cr, uid, lead_id, attachments, context=None):
        if context is None:
            context = {}

        ir_attach_o = self.pool.get("ir.attachment")

        for attachment in attachments:
            values = {
                "res_model": "giscedata.crm.lead",
                "res_id": lead_id,
                "datas_fname": attachment["filename"],
                "name": attachment["filename"],
                "category_id": self._get_category_id(cr, uid, attachment["category"]),
                "datas": attachment["datas"]
            }
            ir_attach_o.create(cr, uid, values, context=context)

    def _get_category_id(self, cr, uid, category_code, context=None):
        if context is None:
            context = {}

        ir_attach_categ_o = self.pool.get("ir.attachment.category")

        categ_id = ir_attach_categ_o.search(
            cr, uid, [("code", "=", category_code)], context=context
        )[0]

        return categ_id

    def _save_www_data_in_history(self, cr, uid, lead_id, www_vals, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get("giscedata.crm.lead")
        lead = lead_o.browse(cr, uid, lead_id, context=context)

        www_vals = copy.deepcopy(www_vals)  # Avoid modifying the original dict
        for attachment in www_vals.get("attachments", []):
            # Remove the attachment base64 data from the log
            attachment.pop("datas", None)

        # giscedata_switching/giscedata_polissa.crear_cas_atr reads the contract observations
        # and looks for the key 'proces: XX' :O
        www_vals['contract_info']['proces'] = www_vals['contract_info']['process']

        data = yaml.safe_dump(www_vals, indent=2)
        msg = "{header}\n{data}".format(header=WWW_DATA_FORM_HEADER, data=data)
        lead.historize_msg(msg, context=context)

    def _check_lead_can_be_activated(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get("giscedata.crm.lead")
        lead = lead_o.browse(cr, uid, lead_id, context=context)

        savepoint = 'savepoint_check_lead_can_be_activated_{}'.format(id(cr))
        cr.savepoint(savepoint)

        ctxt = context.copy()
        ctxt['in_rollback_transaction'] = True
        error = None
        try:
            if lead.billing_payment_method == "card_recurrent" and not lead.creditcard_token:
                lead_o.write(
                    cr,
                    uid,
                    lead_id,
                    self._get_validation_card_values(lead_id),
                    context=ctxt,
                )
            lead_o.force_validation(cr, uid, [lead_id], context=ctxt)
            lead_o.create_entities(cr, uid, lead_id, context=ctxt)
            cr.rollback(savepoint)
        except Exception as e:
            cr.rollback(savepoint)
            exc_type, exc_value, exc_tb = sys.exc_info()
            error = dict(
                error=str(e),
                code="Unactivable",
                trace=traceback.format_exception(exc_type, exc_value, exc_tb),
            )

        return error

    def _get_validation_card_values(self, lead_id):
        return {
            "creditcard_token": "validation-token-{}".format(lead_id),
            "creditcard_masked_number": "**** **** **** 0000",
            "creditcard_expiry_date": "12/30",
            "creditcard_cof_txnid": "validation-cof-{}".format(lead_id),
        }

    def _already_has_contract(self, cr, uid, vat, context=None):
        if context is None:
            context = {}
        partner_o = self.pool.get("res.partner")
        polissa_o = self.pool.get("giscedata.polissa")
        result = False
        partner_id = partner_o.search(cr, uid, [('vat', '=', vat)])
        if partner_id:
            context["active_test"] = False
            if polissa_o.search(cr, uid, [("titular", "=", partner_id[0])], context=context):
                result = True
            context.pop("active_test")
        return result

    def _check_member_vat_dont_exists(self, cr, uid, vat, context=None):
        if context is None:
            context = {}

        partner_o = self.pool.get("res.partner")
        ir_model_o = self.pool.get("ir.model.data")

        vat = 'ES%s' % vat.upper()
        member_category_id = ir_model_o.get_object_reference(
            cr, uid, "som_partner_account", "res_partner_category_soci")[1]

        partner_id = partner_o.search(cr, uid, [
            ('vat', '=', vat),
            ('ref', '=like', 'S%'),
            ('category_id', 'in', [member_category_id]),
        ])
        if partner_id:
            raise osv.except_osv(
                "INVALID_VAT",
                "An existing partner ({}) was found with VAT {}".format(partner_id, vat)
            )

    def _check_member_vat_number_matching(self, cr, uid, vat, number, context=None):
        if context is None:
            context = {}

        member_o = self.pool.get("somenergia.soci")

        member_www_soci = None
        vat = 'ES%s' % vat.upper()

        member_id = member_o.search(cr, uid, [('vat', '=', vat)])
        if member_id:
            member_www_soci = member_o.read(cr, uid, member_id[0], ['www_soci'])['www_soci']

        member_found = member_id and member_www_soci == number
        if not member_found:
            raise osv.except_osv(
                "INVALID_MEMBER",
                "Member has been not found: {} not match with VAT {}".format(number, vat)
            )
        return member_id[0]

    def _split_phone_prefix(self, cursor, uid, phone_full, context=None):
        """Splits (if possible) the phone number and prefix using the prefixes table"""
        phone_prefix_o = self.pool.get('res.phone.national.code')
        if not phone_full:
            return None, None
        parts = phone_full.split(' ', 1)
        if len(parts) == 2 and parts[0].startswith('+'):
            prefix_res = phone_prefix_o.search(cursor, uid, [('name', '=', parts[0])], limit=1)
            return prefix_res and prefix_res[0] or None, parts[1]
        return None, phone_full

    def sign_lead(self, cr, uid, lead_id, cups, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get('giscedata.crm.lead')
        process_o = self.pool.get('giscedata.signatura.process')
        lead_data = lead_o.read(
            cr, uid, lead_id, ["cups", "signature_process", "lang"], context=context
        )
        lead_cups = (lead_data.get('cups') or '').strip().upper()
        requested_cups = (cups or '').strip().upper()

        if not requested_cups or lead_cups != requested_cups:
            raise osv.except_osv(
                'Error',
                'Lead {} does not match CUPS {}'.format(lead_id, cups)
            )

        signature_process = lead_data.get("signature_process")
        if signature_process:
            process_data = process_o.read(
                cr, uid, signature_process[0], ['signature_url', 'status'], context=context
            )
            signature_url = process_data.get('signature_url')
            return {'url': signature_url}

        ctx = context.copy()
        ctx['delivery_type'] = 'url'
        ctx['provider'] = 'signaturit'

        cr.commit()

        # `start_signature_process` creates signature artifacts with admin-only
        # permissions in this legacy flow, so we keep the original user id while
        # temporarily elevating the group context.
        with Sudo(uid=uid, gid=0):
            with self.api.db.cursor() as sign_cursor:
                process_id = lead_o.start_signature_process(
                    sign_cursor, uid, lead_id, context=ctx
                )

        if not process_id:
            raise osv.except_osv(
                'Error',
                'Signature process could not be started for lead {}'.format(lead_id)
            )

        timeout_seconds = 200.0
        poll_interval = 0.2
        deadline = time.time() + timeout_seconds
        signature_url = False

        while time.time() < deadline:
            process_data = process_o.read(
                cr, uid, process_id, ['signature_url', 'status'], context=context
            )
            signature_url = process_data.get('signature_url')
            if signature_url:
                break
            if process_data.get('status') in self._SIGNATURE_ERROR_STATUSES:
                raise osv.except_osv(
                    'Error',
                    (
                        'Signature process failed before URL generation '
                        '(process_id={}, status={})'
                    ).format(process_id, process_data.get('status'))
                )
            time.sleep(poll_interval)

        if not signature_url:
            raise osv.except_osv(
                'Error',
                'Timeout waiting signature URL (process_id={})'.format(process_id)
            )

        lang = lead_data.get('lang').split('_')[0]

        signature_url = signature_url.replace("app.", "sign-app.")
        signature_url = signature_url.replace("document", "v1/{}".format(lang))

        return {'url': signature_url}


SomLeadWww()
