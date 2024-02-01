class main:
    def _get_formatted_address(self, cursor, uid, address):
        data = {}
        data["creditor_address"] = " ".join([str(address.street) if address.street else ""])
        data["creditor_province"] = str(address.state_id.name) if address.state_id else ""
        data["creditor_country"] = address.country_id.name
        data["creditor_city"] = address.city
        data["creditor_zip"] = str(address.zip)
        return data

    def _get_swift_code(self, cursor, uid, iban):
        res_bank_obj = self.pool.get("res.partner.bank")

        pbank_ids = res_bank_obj.search(cursor, uid, [("iban", "=", iban)])
        if not pbank_ids:
            return ""

        return res_bank_obj.browse(cursor, uid, pbank_ids[0]).bank.bic

    def _is_business(self, cursor, uid, object):
        vat = object.debtor_vat[2:] if object.debtor_vat.startswith("ES") else object.debtor_vat
        vat_is_company = vat[0] not in "0123456789KLMXYZ"
        if not isinstance(object.reference, str):
            return vat_is_company

        model_name, obj_id = object.reference.split(",")
        if model_name != "giscedata.polissa":
            return vat_is_company

        pol_o = self.get("giscedata.polissa")
        cnae_is_domestic = pol_o.read(cursor, uid, obj_id, ["cnae"])["cnae"][1] == "9820"

        return vat_is_company or not cnae_is_domestic

    def get_data(self, cursor, uid, object, extra_text, context):
        data = {}

        """
        # creditor data
        data['creditor_code'] = object.creditor_code
        data['order_reference'] = object.name
        data['creditor_name'] = object.creditor_id.name
        data.update(self._get_formatted_address(cursor, uid, object.creditor_id.partner_id.address[0]))

        # debtor data
        data['debtor_name'] = object.debtor_name
        data['debtor_address'] = object.debtor_address
        data['debtor_province'] = object.debtor_state
        data['debtor_country'] = object.debtor_country
        data['debtor_iban_print'] = object.debtor_iban_print
        data['recurring'] = "checked" if object.payment_type == 'recurring' else ''
        data['single_payment'] = "checked" if not data['recurring'] else ''
        data['swift'] = self._get_swift_code(cursor, uid, object.debtor_iban)

        data_firma = datetime.strptime(object.date, '%Y-%m-%d') if object.date else datetime.now()
        data['sign_date'] = babel.dates.format_datetime(data_firma, "d LLLL 'de' YYYY", locale='es_ES')
        data['is_business'] = self._is_business(cursor, uid, object)
        """
        par_obj = object.pool.get("res.partner")
        som_par = par_obj.browse(cursor, uid, 1)

        # creditor data
        data["creditor_code"] = "ES24000F55091367"  # object.creditor_code
        data["order_reference"] = ""  # object.name
        data["creditor_name"] = "SOM ENERGIA SCCL"  # object.creditor_id.name
        data.update(self._get_formatted_address(cursor, uid, som_par.address[0]))

        # debtor data
        data["debtor_name"] = ""
        data["debtor_address"] = ""
        data["debtor_province"] = ""
        data["debtor_country"] = ""
        data["debtor_iban_print"] = ""
        data["debtor_city"] = ""
        data["recurring"] = "checked"
        data["single_payment"] = ""
        data["swift"] = ""
        data["sign_date"] = ""
        data["is_business"] = True
        data["lang"] = object.lang

        return data
