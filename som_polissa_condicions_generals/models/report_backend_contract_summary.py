# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

from datetime import datetime

from report_backend.report_backend import report_browsify

from .report_backend_ccpp import ReportBackendCondicionsParticulars


CARD_PAYMENT_TYPE = "COBRAMENT_RECURRENT_TARGETA"
CARD_FALLBACK_LITERAL = (
    u"Tarjeta de crédito (pago seleccionado mediante tarjeta bancaria)"
)


class ReportBackendContractSummary(ReportBackendCondicionsParticulars):
    _name = "report.backend.contract.summary"

    def _get_summary_context(self, context=None):
        context = (context or {}).copy()
        context.pop("tarifa_provisional", None)
        return context

    def _get_lang_from_context(self, context, pol):
        if context and context.get("lang"):
            return context["lang"]
        if pol.titular:
            return pol.titular.lang or "es_ES"
        return "es_ES"

    def _extract_last_4_digits(self, value):
        value = value or ""
        digits = "".join([character for character in value if character.isdigit()])
        return digits[-4:] if len(digits) >= 4 else ""

    def _is_autoconsum_active(self, pol):
        return getattr(pol, "tipus_subseccio", False) not in (False, "", "00", "0C")

    def get_duration_text(self, today=None):
        today = today or datetime.today()
        quarter = ((today.month - 1) // 3) + 1
        return u"{}º trimestre {}".format(int(quarter), today.year)

    def get_payment_data(self, cursor, uid, pol, context=None):
        payment_type = getattr(pol, "tipo_pago", False)
        is_card = bool(payment_type and payment_type.code == CARD_PAYMENT_TYPE)
        label = ""
        last4 = ""

        if is_card:
            masked_number = getattr(getattr(pol, "creditcard", False), "masked_number", "")
            last4 = self._extract_last_4_digits(masked_number)
            label = last4 or CARD_FALLBACK_LITERAL
        else:
            printable_iban = getattr(getattr(pol, "bank", False), "printable_iban", "")
            last4 = self._extract_last_4_digits(printable_iban)
            label = last4

        return {
            "is_card": is_card,
            "label": label,
            "last4": last4,
        }

    def get_polissa_data(self, cursor, uid, pol, context=None):
        return super(ReportBackendContractSummary, self).get_polissa_data(
            cursor, uid, pol, context=self._get_summary_context(context)
        )

    def get_prices_data(self, cursor, uid, pol, context=None):
        return super(ReportBackendContractSummary, self).get_prices_data(
            cursor, uid, pol, context=self._get_summary_context(context)
        )

    def get_gurb_summary_data(self, cursor, uid, pol, context=None):
        return False

    def get_section_flags(self, cursor, uid, pol, context=None):
        has_generation = bool(getattr(pol, "te_assignacio_gkwh", False))
        gurb_data = self.get_gurb_summary_data(cursor, uid, pol, context=context)
        has_gurb = bool(gurb_data)
        return {
            "has_autoconsum": self._is_autoconsum_active(pol),
            "has_generation": has_generation,
            "has_gurb": has_gurb,
            "show_section_6_final_paragraph": has_gurb,
            "show_section_7_final_paragraph": has_generation or has_gurb,
            "gurb": gurb_data,
        }

    def get_company_data(self):
        return {
            "name": "SOM ENERGIA S.C.C.L",
            "brand": "SOM ENERGIA",
            "vat": "F55091367",
            "address": "C/ Riu Güell, 68, 17005 - Girona",
            "postal_address": "C/ Riu Güell, 68, 17005 - Girona",
            "email": "info@somenergia.coop",
            "phone": "900.103.605",
        }

    def get_holder_data(self, pol, context=None):
        holder_address = pol.titular and pol.titular.address and pol.titular.address[0] or False
        return {
            "name": pol.titular and pol.titular.name or "",
            "vat": pol.titular and (pol.titular.vat or "").replace("ES", "") or "",
            "street": holder_address and holder_address.street or "",
            "zip": holder_address and holder_address.zip or "",
            "city": holder_address and holder_address.city or "",
            "phone": holder_address and holder_address.phone or "",
            "lang": self._get_lang_from_context(context, pol),
        }

    def get_supply_data(self, pol):
        supply = {
            "address": pol.cups and pol.cups.direccio or "",
            "province": pol.cups and pol.cups.id_provincia and pol.cups.id_provincia.name or "",
            "country": pol.cups and pol.cups.id_provincia and pol.cups.id_provincia.country_id and pol.cups.id_provincia.country_id.name or "",  # noqa: E501
            "cups": pol.cups and pol.cups.name or "",
            "cnae": pol.cnae and pol.cnae.name or "",
        }
        cadastral_reference = pol.cups and getattr(pol.cups, "ref_catastral", False) or False
        contract_number = getattr(pol, "name", False)
        if cadastral_reference:
            supply["cadastral_reference"] = cadastral_reference
        if contract_number:
            supply["contract_number"] = contract_number
        return supply

    def get_self_consumption_data(self, cursor, uid, pol, context=None):
        if not self._is_autoconsum_active(pol):
            return False

        autoconsum = getattr(pol, "autoconsum_id", False)
        return {
            "cau": autoconsum and getattr(autoconsum, "cau", False) or False,
            "collective": autoconsum and getattr(autoconsum, "collectiu", False) or False,
        }

    def get_economic_summary(self, prices, features):
        pricelists = prices.get("pricelists", [])
        pricelist = pricelists and pricelists[0] or {}
        power_prices = []
        for period, value in sorted(pricelist.get("power_prices_untaxed", {}).items()):
            power_prices.append({"period": period, "value": value})

        energy_prices = []
        for period, value in sorted(pricelist.get("energy_prices_untaxed", {}).items()):
            energy_prices.append({"period": period, "value": value})

        generation_prices = []
        if features["has_generation"]:
            for period, value in sorted(pricelist.get("generation_prices_untaxed", {}).items()):
                generation_prices.append({"period": period, "value": value})

        return {
            "is_indexed": prices.get("mostra_indexada", False),
            "validity_text": pricelist.get("text_vigencia", ""),
            "tax_text": pricelist.get("text_impostos", ""),
            "power_prices": power_prices,
            "energy_prices": energy_prices,
            "generation_prices": generation_prices,
            "cooperative_fee": pricelist.get(
                "coeficient_k_untaxed",
                prices.get("coeficient_k_untaxed", False),
            ),
            "autoconsum_price": pricelist.get("price_auto_untaxed", False),
        }

    def get_offer_data(self, cursor, uid, pol, prices, context=None):
        polissa_data = self.get_polissa_data(cursor, uid, pol, context=context)
        potencies_data = self.get_potencies_data(cursor, uid, pol, None, context=context)
        features = self.get_section_flags(cursor, uid, pol, context=context)
        tariff_parts = [polissa_data.get("tarifa_mostrar", ""), polissa_data.get("tarifa", "")]
        tariff_label = u" ".join([part for part in tariff_parts if part])
        if features["has_generation"]:
            tariff_label = u"{} / Generation".format(tariff_label)

        visible_powers = []
        for periode in potencies_data.get("periodes", []):
            if not periode:
                continue
            period_code, power = periode
            if not power:
                continue
            visible_powers.append({
                "period": "P{}".format(period_code),
                "power": power,
            })

        return {
            "tariff_label": tariff_label,
            "duration_text": self.get_duration_text(),
            "powers": visible_powers,
            "economic_summary": self.get_economic_summary(prices, features),
        }

    def get_discount_data(self, cursor, uid, pol, context=None):
        has_autoconsum = self._is_autoconsum_active(pol)
        return {
            "text": "N/A" if not has_autoconsum else (
                u"En caso de que se te aplique el descuento flux solar se informará del mismo a la siguiente factura a aquella en la que no haya sido posible compensar todo el valor económico de los excedentes de la instalación de autoconsumo."  # noqa: E501
            ),
            "show_legal_text": has_autoconsum,
        }

    def get_cnmc_data(self, cursor, uid, pol, context=None):
        return {
            "is_visible": True,
            "lang": self._get_lang_from_context(context, pol).lower(),
            "link_qr": "https://comparador.cnmc.gob.es/",
            "has_gkwh": bool(getattr(pol, "te_assignacio_gkwh", False)),
        }

    @report_browsify
    def get_data(self, cursor, uid, pol, context=None):
        context = self._get_summary_context(context)
        features = self.get_section_flags(cursor, uid, pol, context=context)
        prices = self.get_prices_data(cursor, uid, pol, context=context)
        payment = self.get_payment_data(cursor, uid, pol, context=context)
        self_consumption = self.get_self_consumption_data(cursor, uid, pol, context=context)
        data = {
            "company": self.get_company_data(),
            "holder": self.get_holder_data(pol, context=context),
            "supply": self.get_supply_data(pol),
            "offer": self.get_offer_data(cursor, uid, pol, prices, context=context),
            "prices": prices,
            "payment": payment,
            "discounts": self.get_discount_data(cursor, uid, pol, context=context),
            "features": features,
            "self_consumption": self_consumption,
            "cnmc": self.get_cnmc_data(cursor, uid, pol, context=context),
            "bono_social_estimate": "",
            "gurb": features["gurb"],
        }
        return data


ReportBackendContractSummary()
