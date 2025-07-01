# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from mako.template import Template
from datetime import date


class ReportBackendInvoiceEmail(ReportBackend):
    _source_model = "giscedata.facturacio.factura"
    _name = "report.backend.invoice.email"

    @report_browsify
    def get_data(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}

        data = {
            "comerci": self.get_comerci(cursor, uid, fra, context=context),
            "polissa": self.get_polissa(cursor, uid, fra, context=context),
            "factura": self.get_factura(cursor, uid, fra, context=context),
            "socia": self.get_socia(cursor, uid, fra, context=context),
            "linies": self.get_linies(cursor, uid, fra, context=context),
            "text_correu": self.get_text_correu(cursor, uid, fra, context=context),
            "lang": fra.partner_id.lang,
        }

        return data

    def get_lang(self, cursor, uid, record_id, context=None):
        if context is None:
            context = {}

        fact_o = self.pool.get("giscedata.facturacio.factura")
        fact_br = fact_o.browse(cursor, uid, record_id, context=context)

        return fact_br.partner_id.lang

    def get_comerci(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}
        energetica = self.get_socia(cursor, uid, fra, context=context)["energetica"]

        data = {}

        if energetica:
            data[
                "dark_logo"
            ] = "https://www.somenergia.coop/factura/logo-factura-energetica-fosc.png"  # noqa: E501
            data[
                "light_logo"
            ] = "https://www.somenergia.coop/factura/logo-factura-energetica-clar.png"  # noqa: E501

        return data

    def get_socia(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}
        data = {"socia": fra.polissa_id.soci.id, "energetica": fra.polissa_id.soci.id == 38039}

        return data

    def _isTariffChange(self, cursor, uid, fra, context=None):
        ppu = {}
        for line in fra.linies_energia:
            if line.name in ppu:
                if line.price_unit != ppu[line.name]:
                    return True
            else:
                ppu[line.name] = line.price_unit
        ppu = {}
        for line in fra.linies_potencia:
            if line.name in ppu:
                if line.price_unit != ppu[line.name]:
                    return True
            else:
                ppu[line.name] = line.price_unit
        return False

    def _flag_message_replacecement_counters_edistri(self, cursor, uid, fra, context=None):
        date_from = date(2025, 2, 1)
        date_to = date(2025, 4, 30)
        id_edistri = 2273  # hardcoded because not xml_id found
        if date_from <= date.today() <= date_to and fra.polissa_id.distribuidora.id == id_edistri:
            return True
        else:
            return False

    def get_factura(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}

        report_o = self.pool.get("giscedata.facturacio.factura.report.v2")
        data = report_o.get_factura(cursor, uid, fra, context=context)

        data["isTariffChange"] = self._isTariffChange(cursor, uid, fra, context=context)

        return data

    def get_linies(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}

        report_o = self.pool.get("giscedata.facturacio.factura.report.v2")
        data = report_o.get_linies(cursor, uid, fra, context=context)

        return data

    def get_polissa(self, cursor, uid, fra, context=None):
        if context is None:
            context = {}

        report_o = self.pool.get("giscedata.facturacio.factura.report.v2")
        polissa_categ_o = self.pool.get("giscedata.polissa.category")
        cups_o = self.pool.get("giscedata.cups.ps")
        imd_o = self.pool.get("ir.model.data")

        data = report_o.get_polissa(cursor, uid, fra, context=context)

        polissa_retrocedida = False
        de_lot = fra.lot_facturacio and fra.lot_facturacio.id != False  # noqa: E712
        if de_lot:
            clot_obj = fra.pool.get("giscedata.facturacio.contracte_lot")
            clot_id = clot_obj.search(
                fra._cr,
                fra._uid,
                [("polissa_id", "=", fra.polissa_id.id), ("lot_id", "=", fra.lot_facturacio.id)],
            )
            if clot_id:
                n_retrocedir_lot = clot_obj.read(
                    fra._cr, fra._uid, clot_id[0], ["n_retrocedir_lot"]
                )["n_retrocedir_lot"]
                polissa_retrocedida = n_retrocedir_lot > 0

        data["polissa_retrocedida"] = polissa_retrocedida

        polissa_categ_id = imd_o.get_object_reference(
            cursor, uid, "som_polissa", "categ_tarifa_empresa"
        )[1]
        polissa_categ = polissa_categ_o.browse(cursor, uid, polissa_categ_id)
        data["has_business_tariff"] = polissa_categ in fra.polissa_id.category_id

        cups_id = cups_o.search(fra._cr, fra._uid, [('name', '=', data["cups"]["codi"])])
        cups = cups_o.browse(fra._cr, fra._uid, cups_id)[0]
        data["cups"]["is_peninsula"] = cups.id_municipi.subsistema_id.code == "PE"
        data["flag_msg_counters_edistri"] = self._flag_message_replacecement_counters_edistri(
            cursor, uid, fra, context=context
        )

        return data

    def get_text_correu(self, cursor, uid, fra, context=None):
        def render(text_to_render, object_):
            templ = Template(text_to_render)
            return templ.render_unicode(object=object_, format_exceptions=True)

        if context is None:
            context = {}

        data = {}

        t_obj = self.pool.get("poweremail.templates")
        md_obj = self.pool.get("ir.model.data")

        template_id = md_obj.get_object_reference(
            cursor, uid, "som_poweremail_common_templates", "common_template_legal_footer"
        )[1]
        data["text_legal"] = render(
            t_obj.read(cursor, uid, [template_id], ["def_body_text"])[0]["def_body_text"], fra
        )

        return data


ReportBackendInvoiceEmail()
