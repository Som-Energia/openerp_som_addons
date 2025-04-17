# -*- encoding: utf-8 -*-
import traceback
import sys
from osv import osv
from datetime import datetime
import yaml

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

        tensio_230 = imd_o.get_object_reference(cr, uid, 'giscedata_tensions', 'tensio_230')[1]

        tarifa_id = tarifa_o.search(cr, uid, [("name", "=", contract_info["tariff"])])[0]
        payment_mode_id = payment_mode_o.search(cr, uid, [("name", "=", "ENGINYERS")])[0]
        cnae_id = cnae_o.search(cr, uid, [("name", "=", contract_info["cnae"])])[0]
        tariff_mode = 'index' if contract_info["is_indexed"] else 'atr'
        llista_preu_id = polissa_o.get_pricelist_from_tariff_and_location(
            cr, uid, contract_info["tariff"], tariff_mode, contract_address["city_id"], context).id

        distri_ref = cups_ps_o.partner_map_from_cups(
            cr, uid, contract_info["cups"], context=context)

        # TODO: In the future, this needs to accept also not new members
        member = www_vals["new_member_info"]

        values = {
            "state": "open",
            "name": "{} / {}".format(member["vat"].upper(), contract_info["cups"]),
            "lang": member["lang"],
            "cups": contract_info["cups"],
            "codigoEmpresaDistribuidora": distri_ref,
            # "cups_ref_catastral": www_vals.get("cups_cadastral_reference"), TODO test
            "cups_zip": contract_address["postal_code"],
            "cups_id_municipi": contract_address["city_id"],
            "cups_nv": contract_address["street"],
            "cups_pnp": contract_address.get("number"),
            "cups_pt": contract_address.get("floor"),
            "cups_es": contract_address.get("stair"),
            "cups_pu": contract_address.get("door"),
            "cups_bq": contract_address.get("block"),
            "cnae": cnae_id,
            "data_alta_prevista": datetime.today().strftime('%Y-%m-%d'),
            "tarifa": tarifa_id,
            "facturacio_potencia": 'max' if contract_info["tariff"] == '3.0TD' else 'icp',
            "tensio_normalitzada": tensio_230,  # TODO check if always work
            "atr_proces_name": contract_info['process'],
            "change_adm": contract_info['process'] == 'C2',
            "contract_type": self._CONTRACT_TYPE_ANUAL,
            "llista_preu": llista_preu_id,
            "facturacio": self._FACTURACIO_MENSUAL,
            "iban": www_vals["iban"],
            "payment_mode_id": payment_mode_id,
            "enviament": "email",
            "create_new_member": www_vals["linked_member"] == "new_member",
            "autoconsumo": "00",  # Without self-consumption by default
            "titular_vat": 'ES%s' % member["vat"].upper(),
            "titular_nom": member["name"],
            "titular_cognom1": member.get("surname"),
            "tipus_vivenda": 'habitual',
            "titular_zip": member["address"]["postal_code"],
            "titular_nv": member["address"]["street"],
            "titular_pnp": member["address"].get("number"),
            "titular_pt": member["address"].get("floor"),
            "titular_es": member["address"].get("stair"),
            "titular_pu": member["address"].get("door"),
            "titular_bq": member["address"].get("block"),
            "titular_id_municipi": member["address"]["city_id"],
            "titular_email": member["email"],
            "titular_phone": member["phone"],
            "titular_mobile": member.get("phone2"),
            "use_cont_address": False,
            "donation": www_vals.get("donation", False),
            "member_quota_payment_type": www_vals.get("member_payment_type")
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

        if member["is_juridic"]:
            values["persona_firmant_vat"] = member["proxy_vat"]
            values["persona_nom"] = member["proxy_name"]

        for i, power in enumerate(contract_info["powers"]):
            values["potenciasContratadasEnKWP%s" % str(i + 1)] = float(power) / 1000

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


SomLeadWww()
