# -*- coding: utf-8 -*-
from osv import osv

import babel
from datetime import datetime


class PaymentMandate(osv.osv):
    _name = "payment.mandate"
    _inherit = "payment.mandate"

    def _get_formatted_address(self, cursor, uid, address):
        data = {}
        data["creditor_address"] = " ".join(
            [
                str(address.street) if address.street else "",
                str(address.zip) if address.zip else "",
                str(address.city) if address.city else "",
            ]
        )
        data["creditor_province"] = str(address.state_id.name) if address.state_id else ""
        data["creditor_country"] = address.country_id.name
        data["creditor_city"] = address.city

        return data

    def _is_business(self, cursor, uid, mandate):
        vat = mandate.debtor_vat[2:] if mandate.debtor_vat.startswith("ES") else mandate.debtor_vat
        vat_is_company = vat[0] not in "0123456789KLMXYZ"
        if not isinstance(mandate.reference, str):
            return vat_is_company

        model_name, obj_id = mandate.reference.split(",")
        if model_name != "giscedata.polissa":
            return vat_is_company

        pol_o = self.get("giscedata.polissa")
        cnae_is_domestic = pol_o.read(cursor, uid, obj_id, ["cnae"])["cnae"][1] == "9820"
        return vat_is_company or not cnae_is_domestic

    def sepa_particulars_data(self, cursor, uid, ids):
        if not ids:
            raise Exception("No payment mandate id provided")

        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        mandate = self.browse(cursor, uid, ids)
        data = {}

        # creditor data
        data["creditor_code"] = mandate.creditor_code
        data["order_reference"] = mandate.name
        data["creditor_name"] = mandate.creditor_id.name
        data.update(
            self._get_formatted_address(cursor, uid, mandate.creditor_id.partner_id.address[0])
        )

        # debtor data
        data["debtor_name"] = mandate.debtor_name
        data["debtor_address"] = mandate.debtor_address
        data["debtor_province"] = mandate.debtor_state
        data["debtor_country"] = mandate.debtor_country
        data["debtor_iban_print"] = mandate.debtor_iban_print
        data["recurring"] = "checked" if mandate.payment_type == "recurring" else ""
        data["single_payment"] = "checked" if not data["recurring"] else ""
        data["swift"] = self._get_swift_code(cursor, uid, mandate.debtor_iban)

        data_firma = datetime.strptime(mandate.date, "%Y-%m-%d") if mandate.date else datetime.now()
        data["sign_date"] = babel.dates.format_datetime(
            data_firma, "d LLLL 'de' YYYY", locale="es_ES"
        )
        data["is_business"] = self._is_business(cursor, uid, mandate)

        return data


PaymentMandate()
