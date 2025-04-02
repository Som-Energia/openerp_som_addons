# -*- encoding: utf-8 -*-
from osv import osv
from datetime import datetime

from giscedata_cups.dso_cups.cups import get_distri_vals, get_dso
from gestionatr.defs import conv_dict_5, conv_dict_6


class SomLeadWww(osv.osv_memory):
    _name = "som.lead.www"

    _CONTRACT_TYPE_ANUAL = '01'
    _FACTURACIO_MENSUAL = 1

    def create_lead(self, cr, uid, www_vals, context=None):
        if context is None:
            context = {}
        imd_o = self.pool.get("ir.model.data")
        lead_o = self.pool.get("giscedata.crm.lead")
        payment_mode_o = self.pool.get("payment.mode")
        polissa_o = self.pool.get("giscedata.polissa")
        tarifa_o = self.pool.get("giscedata.polissa.tarifa")
        cnae_o = self.pool.get("giscemisc.cnae")

        tensio_230 = imd_o.get_object_reference(cr, uid, 'giscedata_tensions', 'tensio_230')[1]

        tarifa_id = tarifa_o.search(cr, uid, [("name", "=", www_vals["tariff"])])[0]
        payment_mode_id = payment_mode_o.search(cr, uid, [("name", "=", "ENGINYERS")])[0]
        cnae_id = cnae_o.search(cr, uid, [("name", "=", www_vals["cnae"])])[0]
        tariff_mode = 'index' if www_vals["is_indexed"] else 'atr'
        llista_preu_id = polissa_o.get_pricelist_from_tariff_and_location(
            cr, uid, www_vals["tariff"], tariff_mode, www_vals["cups_city_id"], context).id

        distri_vals = _get_distri_vals_from_cups(www_vals["cups"])

        # TODO: Cal posar poblacions? (CUPS i titular)
        values = {
            "name": "{} / {}".format(www_vals["contract_member"]["vat"].upper(), www_vals["cups"]),
            "lang": www_vals["contract_member"]["lang"],
            "cups": www_vals["cups"],
            "codigoEmpresaDistribuidora": distri_vals.get("code"),
            "nombreEmpresaDistribuidora": distri_vals.get("name"),
            "distribuidora_vat": distri_vals.get('vat') and 'ES%s' % distri_vals['vat'],
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

        lead_id = lead_o.create(cr, uid, values, context=context)
        return lead_id


def _get_distri_vals_from_cups(cups):
    # based in giscedata_cups_comer -> partner_map_from_cups
    partner_ref = get_dso(cups)
    if partner_ref not in ['0031', '0390']:
        # Original get_distri_vals that do not use the conversion dicts
        return get_distri_vals(cups)

    # In this case we return only the code and rely the distri will be in the bbdd
    distri_vals = {}
    cups_ref = cups[2:8]
    if cups_ref[:5] == '00314':
        if cups_ref[:6] == '003144':
            # hidroelèctrica de l'empordà
            distri_vals['code'] = '0396'
        else:
            distri_vals['code'] = '0024'

    if cups_ref[:5] in conv_dict_5:
        distri_vals['code'] = conv_dict_5[cups_ref[:5]]

    if cups_ref[:6] in conv_dict_6:
        distri_vals['code'] = conv_dict_6[cups_ref[:6]]

    return distri_vals


SomLeadWww()
