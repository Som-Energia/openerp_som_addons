# -*- encoding: utf-8 -*-
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

        tensio_230 = imd_o.get_object_reference(cr, uid, 'giscedata_tensions', 'tensio_230')[1]

        tarifa_id = tarifa_o.search(cr, uid, [("name", "=", www_vals["tariff"])])[0]
        payment_mode_id = payment_mode_o.search(cr, uid, [("name", "=", "ENGINYERS")])[0]
        cnae_id = cnae_o.search(cr, uid, [("name", "=", www_vals["cnae"])])[0]
        tariff_mode = 'index' if www_vals["is_indexed"] else 'atr'
        llista_preu_id = polissa_o.get_pricelist_from_tariff_and_location(
            cr, uid, www_vals["tariff"], tariff_mode, www_vals["cups_city_id"], context).id

        distri_ref = cups_ps_o.partner_map_from_cups(cr, uid, www_vals["cups"], context=context)

        # TODO: Cal posar poblacions? (CUPS i titular)
        values = {
            "name": "{} / {}".format(www_vals["contract_member"]["vat"].upper(), www_vals["cups"]),
            "lang": www_vals["contract_member"]["lang"],
            "cups": www_vals["cups"],
            "codigoEmpresaDistribuidora": distri_ref,
            # "cups_ref_catastral": www_vals.get("cups_cadastral_reference"), TODO test
            "cups_zip": www_vals["cups_postal_code"],
            "cups_id_municipi": www_vals["cups_city_id"],
            "cups_nv": www_vals["cups_address"],
            "cnae": cnae_id,
            "data_alta_prevista": datetime.today().strftime('%Y-%m-%d'),
            "tarifa": tarifa_id,
            "facturacio_potencia": 'max' if www_vals["tariff"] == '3.0TD' else 'icp',
            "tensio_normalitzada": tensio_230,  # TODO check if always work
            "atr_proces_name": www_vals['process'],
            "change_adm": www_vals['process'] == 'C2',
            "contract_type": self._CONTRACT_TYPE_ANUAL,
            "autoconsumo": "00",  # FIXME: use getionatr defs tabla113
            "potenciasContratadasEnKWP1": float(www_vals["power_p1"]) / 1000,
            "potenciasContratadasEnKWP2": float(www_vals["power_p2"]) / 1000,
            "llista_preu": llista_preu_id,
            "facturacio": self._FACTURACIO_MENSUAL,
            "iban": www_vals["payment_iban"],
            "payment_mode_id": payment_mode_id,
            "enviament": "email",
            "owner_is_member": www_vals["owner_is_member"],
            "titular_vat": 'ES%s' % www_vals["contract_member"]["vat"].upper(),
            "titular_nom": www_vals["contract_member"]["name"],
            "titular_cognom1": www_vals["contract_member"].get("surname"),
            "tipus_vivenda": 'habitual',  # TODO: webforms use always habitual, its ok?
            "titular_zip": www_vals["contract_member"]["postal_code"],
            "titular_nv": www_vals["contract_member"]["address"],
            "titular_id_municipi": www_vals["contract_member"]["city_id"],
            "titular_email": www_vals["contract_member"]["email"],
            "titular_phone": www_vals["contract_member"]["phone"],
            "titular_mobile": www_vals["contract_member"].get("phone2"),
            "use_cont_address": False,
            "donation": www_vals.get("donation", False),
            "allow_contact": False,  # TODO: use privacy_conditions? or remove
        }

        if www_vals["contract_member"]["is_juridic"]:
            values["persona_firmant_vat"] = www_vals["contract_member"]["proxy_vat"]
            values["persona_nom"] = www_vals["contract_member"]["proxy_name"]

        if www_vals["tariff"] == "3.0TD":
            values["potenciasContratadasEnKWP3"] = float(www_vals["power_p3"]) / 1000
            values["potenciasContratadasEnKWP4"] = float(www_vals["power_p4"]) / 1000
            values["potenciasContratadasEnKWP5"] = float(www_vals["power_p5"]) / 1000
            values["potenciasContratadasEnKWP6"] = float(www_vals["power_p6"]) / 1000

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
        self.create_attachments(cr, uid, lead_id, www_vals.get("attachments", []), context=context)
        self.save_www_data_in_history(cr, uid, lead_id, www_vals, context=context)
        lead_o.copy_base_attr_gen_from_titular(cr, uid, lead_id)
        return lead_id

    def create_attachments(self, cr, uid, lead_id, attachments, context=None):
        if context is None:
            context = {}

        ir_attach_o = self.pool.get("ir.attachment")

        for attachment in attachments:
            values = {
                "res_model": "giscedata.crm.lead",
                "res_id": lead_id,
                "datas_fname": attachment["filename"],
                "name": attachment["filename"],
                "category_id": self.get_category_id(cr, uid, attachment["category"]),
                "datas": attachment["datas"]
            }
            ir_attach_o.create(cr, uid, values, context=context)

    def get_category_id(self, cr, uid, category_code, context=None):
        if context is None:
            context = {}

        ir_attach_categ_o = self.pool.get("ir.attachment.category")

        categ_id = ir_attach_categ_o.search(
            cr, uid, [("code", "=", category_code)], context=context
        )[0]

        return categ_id

    def save_www_data_in_history(self, cr, uid, lead_id, www_vals, context=None):
        if context is None:
            context = {}

        lead_o = self.pool.get("giscedata.crm.lead")
        lead = lead_o.browse(cr, uid, lead_id, context=context)

        data = yaml.safe_dump(www_vals, indent=2)
        msg = "{header}\n{data}".format(header=WWW_DATA_FORM_HEADER, data=data)
        lead.historize_msg(msg, context=context)


SomLeadWww()
