# -*- encoding: utf-8 -*-
import traceback
import sys
from osv import osv
import yaml
import copy
from oorq.decorators import job

from som_leads_polissa.giscedata_crm_lead import WWW_DATA_FORM_HEADER


class SomLeadWww(osv.osv_memory):
    _name = "som.lead.www"

    _CONTRACT_TYPE_ANUAL = '01'
    _FACTURACIO_MENSUAL = 1
    _127_WITH_SURPLUSES = '2'
    _128_SIMPLIFIED_SURPLUSES = 'a0'
    _131_CONSUMPTION = '01'

    def create_lead(self, cr, uid, www_vals, context=None):
        if context is None:
            context = {}
        imd_o = self.pool.get("ir.model.data")
        lead_o = self.pool.get("giscedata.crm.lead")
        payment_mode_o = self.pool.get("payment.mode")
        polissa_o = self.pool.get("giscedata.polissa")
        tarifa_o = self.pool.get("giscedata.polissa.tarifa")
        cnae_o = self.pool.get("giscemisc.cnae")
        cups_ps_o = self.pool.get("giscedata.cups.ps")
        selfcons_o = self.pool.get("giscedata.autoconsum")
        ir_model_o = self.pool.get("ir.model.data")

        contract_info = www_vals["contract_info"]
        contract_address = contract_info["cups_address"]

        tensio_xml_id = 'tensio_230'
        if contract_info.get("phase") == "3x230/400":
            tensio_xml_id = 'tensio_3x230_400'
        tensio_id = imd_o.get_object_reference(cr, uid, 'giscedata_tensions', tensio_xml_id)[1]

        tarifa_id = tarifa_o.search(cr, uid, [("name", "=", contract_info["tariff"])])[0]
        payment_mode_id = payment_mode_o.search(cr, uid, [("name", "=", "ENGINYERS")])[0]
        tariff_mode = 'index' if contract_info["is_indexed"] else 'atr'
        llista_preu_id = polissa_o.get_pricelist_from_tariff_and_location(
            cr, uid, contract_info["tariff"], tariff_mode, contract_address["city_id"], context).id

        try:
            cnae_id = cnae_o.search(cr, uid, [("name", "=", contract_info["cnae"])])[0]
        except IndexError:
            cnae_id = None  # TODO: Probably new CNAE 2025, by the moment we avoid to fail

        distri_ref = cups_ps_o.partner_map_from_cups(
            cr, uid, contract_info["cups"], context=context)

        member_type = www_vals["linked_member"]

        if member_type == "new_member":
            self._check_member_vat_dont_exists(
                cr, uid, www_vals["new_member_info"]["vat"], context=context)
            member = www_vals["new_member_info"]
        elif member_type in ["sponsored", "already_member"]:
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

            # Complying with the format seq_som_partner_seq format
            member["number"] = "S" + www_vals["linked_member_info"]["code"].zfill(6)
        else:
            raise osv.except_osv(
                "Error",
                "linked_member value not valid: %s" % member_type
            )

        values = {
            "state": "open",
            "name": "{} / {}".format(member["vat"].upper(), contract_info["cups"]),
            "cups": contract_info["cups"],
            "codigoEmpresaDistribuidora": distri_ref,
            "cups_ref_catastral": contract_info.get("cups_cadastral_reference"),
            "cups_zip": contract_address["postal_code"],
            "cups_id_municipi": contract_address["city_id"],
            "cups_nv": contract_address["street"],
            "cups_pnp": contract_address.get("number"),
            "cups_pt": contract_address.get("floor"),
            "cups_es": contract_address.get("stair"),
            "cups_pu": contract_address.get("door"),
            "cups_bq": contract_address.get("block"),
            "cnae": cnae_id,
            "tarifa": tarifa_id,
            "facturacio_potencia": 'max' if contract_info["tariff"] == '3.0TD' else 'icp',
            "tensio_normalitzada": tensio_id,
            "atr_proces_name": contract_info['process'],
            "change_adm": contract_info['process'] == 'C2',
            "contract_type": self._CONTRACT_TYPE_ANUAL,
            "llista_preu": llista_preu_id,
            "facturacio": self._FACTURACIO_MENSUAL,
            "iban": www_vals["iban"],
            "payment_mode_id": payment_mode_id,
            "enviament": "email",
            "create_new_member": member_type == "new_member",
            "autoconsumo": "00",  # Without self-consumption by default
            "member_number": member.get("number"),
            "titular_vat": 'ES%s' % member["vat"].upper(),
            "titular_nom": member.get("name"),
            "titular_cognom1": member.get("surname"),
            "tipus_vivenda": 'habitual',
            "titular_zip": member["address"].get("postal_code"),
            "titular_nv": member["address"].get("street"),
            "titular_pnp": member["address"].get("number"),
            "titular_pt": member["address"].get("floor"),
            "titular_es": member["address"].get("stair"),
            "titular_pu": member["address"].get("door"),
            "titular_bq": member["address"].get("block"),
            "titular_id_municipi": member["address"].get("city_id"),
            "titular_email": member.get("email"),
            "titular_phone": member.get("phone"),
            "titular_mobile": member.get("phone2"),
            "use_cont_address": False,
            "donation": www_vals.get("donation", False),
            "member_quota_payment_type": www_vals.get("member_payment_type"),
            "gender": member.get("gender"),
            "birthdate": member.get("birthdate"),
            "referral_source": member.get("referral_source"),
            "comercial_info_accepted": member.get("comercial_info_accepted", False),
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

        for i, power in enumerate(contract_info["powers"]):
            values["potenciasContratadasEnKWP%s" % str(i + 1)] = float(power) / 1000

        if member.get("lang", False):
            values["lang"] = member["lang"]

        if www_vals.get("self_consumption"):
            values["seccio_registre"] = self._127_WITH_SURPLUSES
            values["subseccio"] = self._128_SIMPLIFIED_SURPLUSES
            values["tipus_cups"] = self._131_CONSUMPTION

            values["cau"] = www_vals["self_consumption"]["cau"]
            values["collectiu"] = www_vals["self_consumption"]["collective_installation"]
            values["tec_generador"] = www_vals["self_consumption"]["technology"]
            values["pot_instalada_gen"] = www_vals["self_consumption"]["installation_power"]
            values["tipus_installacio"] = www_vals["self_consumption"]["installation_type"]
            values["ssaa"] = 'S' if www_vals["self_consumption"]['aux_services'] else 'N'

            values["autoconsumo"] = selfcons_o.get_ree_autoconsum_type_from_attrs(
                values["seccio_registre"], values["subseccio"], int(values["collectiu"]),
                int(values["tipus_cups"]), int(values["tipus_installacio"]), context=context
            )

        # Remove None values to let the lead get them if exists in the bbdd
        for field, value in values.items():
            if value is None:
                del values[field]

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

    def activate_lead(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}

        context["create_draft_atr"] = True

        lead_o = self.pool.get("giscedata.crm.lead")

        msg = lead_o.create_entities(cr, uid, lead_id, context=context)

        lead_o.historize_msg(cr, uid, [lead_id], msg, context=context)
        lead_o.stage_next(cr, uid, [lead_id], context=context)

        if context.get('sync'):
            self._send_mail(cr, uid, lead_id, context=context)
        else:
            self._send_mail_async(cr, uid, lead_id, context=context)

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

        savepoint = 'savepoint_check_lead_can_be_activated_{}'.format(id(cr))
        cr.savepoint(savepoint)

        error = None
        try:
            lead_o.force_validation(cr, uid, [lead_id], context=context)
            lead_o.create_entities(cr, uid, lead_id, context=context)
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

    @job(queue="poweremail_sender")
    def _send_mail_async(self, cr, uid, lead_id, context=None):
        self._send_mail(cr, uid, lead_id, context=context)

    def _send_mail(self, cr, uid, lead_id, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get("giscedata.crm.lead")
        ir_model_o = self.pool.get('ir.model.data')
        template_o = self.pool.get('poweremail.templates')

        lead = lead_o.read(cr, uid, lead_id, ['create_new_member', 'polissa_id'], context=context)

        template_name = "email_contracte_esborrany"
        if lead["create_new_member"]:
            template_name = "email_contracte_esborrany_nou_soci"
        template_id = ir_model_o.get_object_reference(cr, uid, 'som_polissa_soci', template_name)[1]

        polissa_id = lead["polissa_id"][0]
        from_id = template_o.read(cr, uid, template_id)['enforce_from_account'][0]

        wiz_send_obj = self.pool.get("poweremail.send.wizard")
        context.update({
            "active_ids": [polissa_id],
            "active_id": polissa_id,
            "template_id": template_id,
            "src_model": "giscedata.polissa",
            "src_rec_ids": [polissa_id],
            "from": from_id,
            "state": "single",
            "priority": "0",
        })

        params = {"state": "single", "priority": "0", "from": context["from"]}
        wiz_id = wiz_send_obj.create(cr, uid, params, context)
        return wiz_send_obj.send_mail(cr, uid, [wiz_id], context)


SomLeadWww()
