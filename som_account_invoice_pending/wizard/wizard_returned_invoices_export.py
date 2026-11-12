# -*- coding: utf-8 -*-
import base64
import csv
import StringIO
import re

from osv import osv, fields
from datetime import datetime, timedelta, date
from tools.translate import _

HEADERS = [
    "NOMBRE_CORTO",
    "NOMBRE_COMPLETO",
    "MOVIL",
    "EMAIL",
    "ES_EMPRESA",
    "CODIGO_CLIENTE",
    "TITULO",
    "CONCEPTO",
    "FECHA_LIMITE",
    "IMPORTE",
    "IDIOMA",
    "CODIGO_TRANSACCION",
    "DIRECCION",
    "CODIGO_POSTAL",
    "CIUDAD",
    "PAIS",
]


class WizardExportReturnedInvoices(osv.osv_memory):
    _name = "wizard.export.returned.invoices"

    def returned_invoices_export(self, cursor, uid, ids, context=None):
        wizard = self.browse(cursor, uid, ids[0], context)
        fact_ids = context["active_ids"]

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        res_partner_obj = self.pool.get("res.partner")
        imd_obj = self.pool.get("ir.model.data")
        default_process = imd_obj.get_object_reference(
            cursor, uid, "account_invoice_pending", "default_pending_state_process"
        )[1]

        llistat = []

        for fact_id in fact_ids:
            factura = fact_obj.browse(cursor, uid, fact_id)
            partner = factura.partner_id
            nom_sencer = factura.partner_id.name
            nom_curt = res_partner_obj.separa_cognoms(cursor, uid, nom_sencer)["nom"]
            email = partner.www_email
            es_empresa = 1 if factura.pending_state.process_id.id == default_process else 0
            codi_client = partner.vat.replace("ES", "")
            titol = "Factura {} C.{}".format(factura.number, factura.polissa_id.name)
            concepte = "Del {} al {}".format(factura.data_inici, factura.data_final)
            data_limit = datetime.strftime(date.today() + timedelta(days=15), "%Y-%m-%d")
            import_factura = ("%.2f" % factura.residual).replace(".", ",")
            idioma = "ES" if partner.lang == "es_ES" else "CA"
            codi_transaccio = factura.number
            direccio = factura.address_invoice_id.street
            codi_postal = factura.address_invoice_id.zip
            ciutat = factura.address_invoice_id.city
            pais = factura.address_invoice_id.country_id.name

            try:
                telefon = partner.www_mobile if partner.www_mobile else partner.www_phone
                if not telefon:
                    raise
                telefon = "34" + re.sub("[\W_]+", "", telefon)  # noqa: W605
            except Exception:
                raise osv.except_osv(
                    _("DataError"),
                    _("Error en trobar el telefon pel partner {}".format(nom_sencer)),
                )

            llistat.append(
                (
                    nom_curt,
                    nom_sencer,
                    telefon,
                    email,
                    es_empresa,
                    codi_client,
                    titol,
                    concepte,
                    data_limit,
                    import_factura,
                    idioma,
                    codi_transaccio,
                    direccio,
                    codi_postal,
                    ciutat,
                    pais,
                )
            )

        output = StringIO.StringIO()
        writer = csv.writer(output, delimiter=",")
        writer.writerow(HEADERS)

        for row in llistat:
            tmp = [isinstance(t, basestring) and t.encode("utf-8") or t for t in row]  # noqa: F821
            writer.writerow(tmp)

        mfile = base64.b64encode(output.getvalue())

        filename = "returned_invoices_export_%s.csv" % datetime.strftime(
            datetime.today(), u"%Y%m%d"
        )
        wizard.write({"name": filename, "file": mfile, "state": "done"})

    _columns = {
        "name": fields.char("Nom fitxer", size=32),
        "state": fields.char("State", size=16),
        "file": fields.binary("Fitxer"),
    }
    _defaults = {
        "state": lambda *a: "init",
    }


WizardExportReturnedInvoices()
