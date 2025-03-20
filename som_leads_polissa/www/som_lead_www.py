from osv import osv
from datetime import datetime

from giscedata_cups.dso_cups.cups import get_distri_vals


class SomLeadWww(osv.osv_memory):
    _name = "som.lead.www"

    _CONTRACT_TYPE_ANUAL = '01'

    def create_lead(self, cr, uid, www_vals, context=None):
        if context is None:
            context = {}
        imd_o = self.pool.get("ir.model.data")
        lead_o = self.pool.get("giscedata.crm.lead")
        payment_mode_o = self.pool.get("payment.mode")
        tarifa_o = self.pool.get("giscedata.polissa.tarifa")
        cnae_o = self.pool.get("giscemisc.cnae")

        tensio_230 = imd_o.get_object_reference(cr, uid, 'giscedata_tensions', 'tensio_230')[1]

        tarifa_id = tarifa_o.search(cr, uid, [("name", "=", www_vals["tariff"])])[0]
        payment_mode_id = payment_mode_o.search(cr, uid, [("name", "=", "ENGINYERS")])[0]
        cnae_id = cnae_o.search(cr, uid, [("name", "=", www_vals["cnae"])])[0]

        distri_vals = get_distri_vals(www_vals["cups"])

        # TODO: Cal posar poblacions? (CUPS i titular)
        # TODO: Carregar traduccions CAT - ES
        values = {
            "name": "Cunyat",  # TODO: Pensar que posar aqui
            "lang": www_vals["contract_member"]["lang"],
            "cups": www_vals["cups"],
            "codigoEmpresaDistribuidora": distri_vals.get("code"),
            "nombreEmpresaDistribuidora": distri_vals.get("name"),
            "distribuidora_vat": distri_vals['vat'] and 'ES%s' % distri_vals['vat'],
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
            # TODO: other potencias
            # "llista_preu": None,  # FIXME: is mandatory!!! (index o no)
            "facturacio": 1,  # FIXME: remove magic number (mensual)
            "iban": www_vals["payment_iban"],
            "payment_mode_id": payment_mode_id,
            "enviament": "email",
            "titular_vat": 'ES%s' % www_vals["contract_member"]["vat"].upper(),
            "titular_nom": www_vals["contract_member"]["name"],
            "titular_cognom1": www_vals["contract_member"].get("surname"),
            # "tipus_vivenda": None,  # FIXME: habitual or not, is mandatory!!!, mirar cnae
            "titular_zip": www_vals["contract_member"]["postal_code"],
            "titular_nv": www_vals["contract_member"]["address"],
            "titular_id_municipi": www_vals["contract_member"]["city_id"],
            "titular_email": www_vals["contract_member"]["email"],
            "titular_phone": www_vals["contract_member"]["phone"],
            "titular_mobile": www_vals["contract_member"].get("phone2"),  # TODO: test this
            "use_cont_address": False,
            "allow_contact": False,  # FIXME: use privacy_conditions? or remove

            # COSES de www_vals que no s'han fet servir:
            #
            # "owner_is_member": True,
            # "owner_is_payer": True,
            # "contract_member": {
            #     "state_id": 20,
            #     "privacy_conditions": True,
            # },
            # "is_indexed": False,
            # "cups_state_id": 20,
            # "supply_point_accepted": True,
            # "sepa_conditions": True,
            # "donation": False,
            # "general_contract_terms_accepted": True,
            # "particular_contract_terms_accepted": True,
        }
        lead_id = lead_o.create(cr, uid, values, context=context)
        return lead_id


# def _get_full_name(name, surname='', is_juridic=False):
#     full_name = not is_juridic \
#         and '{}, {}'.format(surname, name).strip() \
#         or '{}'.format(name)

#     return full_name.strip()


SomLeadWww()
