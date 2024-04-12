# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from datetime import datetime


class GiscedataFacturacioFacturador(osv.osv):
    """Sobreescrivim el mètode per facturar per incloure el donatiu"""

    _name = "giscedata.facturacio.facturador"
    _inherit = "giscedata.facturacio.facturador"

    def get_donatiu_product(self, cursor, uid, polissa_id, context=None):
        product_obj = self.pool.get("product.product")
        return product_obj.search(cursor, uid, [("default_code", "=", "DN01")])[0]

    def fact_via_lectures(self, cursor, uid, polissa_id, lot_id, context=None):
        """Sobreescrivim el mètode per incloure-hi la línia de factura
        rel·lacionada amb el donatiu si s'escau"""
        if not context:
            context = {}
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        polissa_obj = self.pool.get("giscedata.polissa")
        pricelist_version_o = self.pool.get("product.pricelist.version")
        product_obj = self.pool.get("product.product")
        factures_creades = super(GiscedataFacturacioFacturador, self).fact_via_lectures(
            cursor, uid, polissa_id, lot_id, context
        )
        ctx = context.copy()

        start_date_bo_social = self.pool.get("res.config").get(
            cursor, uid, "som_invoice_start_date_bo_social", "2017-07-01"
        )
        end_date_bo_social = self.pool.get("res.config").get(
            cursor, uid, "som_invoice_end_date_bo_social", "2021-03-31"
        )
        # identificar el producte Bo Social
        pbosocial_ids = product_obj.search(cursor, uid, [("default_code", "=", "BS01")])
        active_bo_social = int(
            self.pool.get("res.config").get(cursor, uid, "som_invoice_active_bo_social", "0")
        )
        pbosocial_id = len(pbosocial_ids) and pbosocial_ids[0]
        fes_bo_social = pbosocial_id and active_bo_social or False

        factures_creades_modificables = []
        donatiu_pol = polissa_obj.read(cursor, uid, polissa_id, ["donatiu"], ctx)["donatiu"]
        if donatiu_pol:
            factures_creades_modificables = factures_creades
        elif fes_bo_social:
            # Si la pòlissa té donatiu, ja són totes modificables
            factures_dates = fact_obj.read(cursor, uid, factures_creades, ["data_inici"], ctx)
            factures_creades_modificables = [
                f["id"]
                for f in factures_dates
                if f["data_inici"] >= start_date_bo_social and f["data_inici"] <= end_date_bo_social
            ]

        if factures_creades_modificables:
            # identificar el producte donacions
            pdona_id = self.get_donatiu_product(cursor, uid, polissa_id, context)

            journal_codes = self.pool.get("res.config").get(
                cursor, uid, "som_invoice_bo_social_journal_codes", ["ENERGIA", "ENERGIA.R"]
            )
            for fact in fact_obj.browse(cursor, uid, factures_creades_modificables, context):
                if fact.journal_id.code in journal_codes:
                    if fact.polissa_id.donatiu:
                        # si la factura és del diari d'energia s'afegeix la línia de
                        # factura rel·lacionada amb el producte donatiu
                        ctx.update({"lang": fact.partner_id.lang})
                        p_br = product_obj.browse(cursor, uid, pdona_id, ctx)
                        # identificar la línia d'energia excloent el preu del MAG (RD 10/2022)
                        kwh = sum(
                            [
                                x.quantity if x.price_unit >= 0 else -x.quantity
                                for x in fact.linia_ids
                                if x.tipus == "energia" and x.product_id.code != "RMAG"
                            ]
                        )
                        kwh = max(kwh, 0.0)
                        vals = {
                            "data_desde": fact.data_inici,
                            "data_fins": fact.data_final,
                            "force_price": 0.01,
                            "uos_id": p_br.uom_id.id,
                            "quantity": kwh,
                            "multi": 1,
                            "product_id": pdona_id,
                            "tipus": "altres",
                            "name": p_br.description,
                        }
                        self.crear_linia(cursor, uid, fact.id, vals, ctx)
                    # Only invoices with start date after 'start_date_bo_social'
                    if (
                        fes_bo_social
                        and fact.data_inici >= start_date_bo_social
                        and fact.data_inici <= end_date_bo_social
                    ):
                        dmn = [
                            ("pricelist_id", "=", fact.llista_preu.id),
                            ("active", "=", True),
                            "|",
                            "|",
                            "|",
                            # El primer detecta aquest cas:
                            # factura:       |-------------|
                            # l.preus: ...---------|
                            "&",
                            ("date_end", ">=", fact.data_inici),
                            ("date_end", "<=", fact.data_final),
                            # El segon detecta aquest altre cas:
                            # factura:       |-------------|
                            # l.preus:             |-------------|
                            # I també aquest altre:
                            # factura:       |-------------|
                            # l.preus:             |-----------...
                            # Tant el primer com el segon domini detecten aquest:
                            # factura:       |-------------|
                            # l.preus:          |-------|
                            "&",
                            ("date_start", ">=", fact.data_inici),
                            ("date_start", "<=", fact.data_final),
                            # El tercer detecta aquest cas:
                            # factura:       |-------------|
                            # l.preus:   |---------------------|
                            "&",
                            ("date_start", "<=", fact.data_inici),
                            ("date_end", ">=", fact.data_final),
                            # I aquest últim:
                            # factura:       |-------------|
                            # l.preus:   |---------------------...
                            "&",
                            ("date_start", "<=", fact.data_inici),
                            ("date_end", "=", False),
                        ]
                        pricelist_version_ids = pricelist_version_o.search(
                            cursor, uid, dmn, context=context
                        )
                        pricelist_version_f = ["date_start", "date_end"]
                        pricelist_version_vs = pricelist_version_o.read(
                            cursor, uid, pricelist_version_ids, pricelist_version_f, context=context
                        )
                        for pricelist_version_v in pricelist_version_vs:
                            # Si la factura és del diari d'energia s'afegeix la
                            # línia de factura rel·lacionada amb el producte Bo
                            # Social.
                            # S'afegeix una linia per cada canvi de preus que hi
                            # hagi
                            ctx.update({"lang": fact.partner_id.lang})
                            p_br = product_obj.browse(cursor, uid, pbosocial_id, ctx)

                            data_desde_plv = datetime.strptime(
                                pricelist_version_v["date_start"], "%Y-%m-%d"
                            )
                            date_bo_social = datetime.strptime(end_date_bo_social, "%Y-%m-%d")
                            if data_desde_plv > date_bo_social:
                                continue

                            data_desde_inv = datetime.strptime(fact.data_inici, "%Y-%m-%d")

                            data_fins_plv = datetime.max
                            if pricelist_version_v["date_end"]:
                                data_fins_plv = datetime.strptime(
                                    pricelist_version_v["date_end"], "%Y-%m-%d"
                                )

                            data_fins_inv = datetime.strptime(fact.data_final, "%Y-%m-%d")

                            data_desde = max(data_desde_plv, data_desde_inv)
                            data_final = min(data_fins_plv, data_fins_inv)

                            vals = {
                                "data_desde": data_desde.strftime("%Y-%m-%d"),
                                "data_fins": data_final.strftime("%Y-%m-%d"),
                                "uos_id": p_br.uom_id.id,
                                "quantity": (data_final - data_desde).days + 1,
                                "multi": 1,
                                "product_id": pbosocial_id,
                                "tipus": "altres",
                                "name": p_br.description,
                            }
                            self.crear_linia(cursor, uid, fact.id, vals, ctx)

        return factures_creades


GiscedataFacturacioFacturador()


class GiscedataFacturacioFactura(osv.osv):
    """Modificació de la factura per poder-la afegir a una remesa"""

    _name = "giscedata.facturacio.factura"
    _inherit = "giscedata.facturacio.factura"

    _columns = {
        "visible_ov": fields.boolean(
            "Visible OV",
            help=_(u"Camp per indicar si la factura " u"sera visible a la Oficina Virtual"),
        )
    }

    _defaults = {"visible_ov": lambda *a: True}


GiscedataFacturacioFactura()
