from osv import osv
from datetime import datetime


class SomLeadWww(osv.osv_memory):
    _name = "som.lead.www"

    def create_lead(self, cr, uid, www_vals, context=None):
        if context is None:
            context = {}
        lead_o = self.pool.get("giscedata.crm.lead")
        tarifa_o = self.pool.get("giscedata.polissa.tarifa")

        tarifa_id = tarifa_o.search(cr, uid, [("name", "=", www_vals["tariff"])])[0]

        # TODO: Cal posar poblacions? (CUPS i titular)
        values = {
            "lang": www_vals["contract_member"]["lang"],
            "cups": www_vals["cups"],
            # "cups_ref_catastral": www_vals.get("cups_cadastral_reference"), TODO test
            "cups_zip": www_vals["cups_postal_code"],
            "cups_id_municipi": www_vals["cups_city_id"],
            "cups_nv": www_vals["cups_address"],
            "cnae": www_vals["cnae"],
            "data_alta_prevista": datetime.today().strftime('%Y-%m-%d'),
            "tarifa": tarifa_id,
            "facturacio_potencia": 'max' if www_vals["tariff"] == '3.0TD' else 'icp',
            "tensio_normalitzada": None,  # FIXME: is mandatory!!!
            "atr_proces_name": www_vals['process'],
            "change_adm": www_vals['process'] == 'C2',
            # "contract_type": "01", # FIXME: use getionatr defs tabla9
            "autoconsumo": "00",  # FIXME: use getionatr defs tabla113
            "potenciasContratadasEnKWP1": float(www_vals["power_p1"]) / 1000,
            "potenciasContratadasEnKWP2": float(www_vals["power_p2"]) / 1000,
            # TODO: other potencias
            "llista_preu": None,  # FIXME: is mandatory!!! (index o no)
            "facturacio": 1,  # FIXME: remove magic number (mensual)
            "iban": www_vals["payment_iban"],
            "payment_mode_id": None,  # FIXME: is mandatory!!!
            "enviament": "email",
            "titular_vat": www_vals["contract_member"]["vat"],
            "titular_nom": _get_full_name(
                www_vals["contract_member"]["name"],
                www_vals["contract_member"]["surname"],
                www_vals["contract_member"]["is_juridic"]
            ),
            "tipus_vivenda": None,  # FIXME: habitual or not, is mandatory!!!, mirar cnae
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


def _get_full_name(name, surname='', is_juridic=False):
    full_name = not is_juridic \
        and '{}, {}'.format(surname, name).strip() \
        or '{}'.format(name)

    return full_name.strip()


SomLeadWww()
