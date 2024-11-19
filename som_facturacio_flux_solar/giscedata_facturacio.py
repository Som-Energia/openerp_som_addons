# -*- coding: utf-8 -*-
from osv import osv


class GiscedataFacturacioFacturador(osv.osv):
    _name = 'giscedata.facturacio.facturador'
    _inherit = 'giscedata.facturacio.facturador'

    def get_max_descompte_total_factura_sense_impostos(  # noqa C901
            self, cursor, uid, factura_id, line_vals, context=None):
        if context is None:
            context = {}

        def uber_round(number):
            return round(round(number, 6), 2)

        imd_obj = self.pool.get('ir.model.data')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        linia_obj = self.pool.get('giscedata.facturacio.factura.linia')

        # Es vol descomptar el total dels conceptes del sector electric
        max_descompte = 0

        # Producte de descompte de la bateria virtual
        product_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio_bateria_virtual",
            "bateria_virtual_product"
        )[1]

        # Si tenen bo social, les linies de bo social s'han de tenir en
        # compte tot i ser de tipus "altres"
        # No es lo millor, pero per dependencies és infinitament més
        # simple fer-ho aqui.
        tenen_bo_social = self.pool.get("ir.module.module").search(
            cursor, uid, [
                ("state", "=", "installed"),
                ('name', '=', 'giscedata_repercusio_bo_social')
            ], context=context
        )

        pbosocial_id = None
        if tenen_bo_social:
            pbosocial_id = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_repercusio_bo_social', 'bosocial_BS01'
            )[1]

        linies_utilitzades_ids = []
        for dict_vals in line_vals:
            if dict_vals['tipus'] not in (
                    'altres', 'subtotal_xml', 'subtotal_xml_ren', 'subtotal_xml_oth'
            ):
                max_descompte += dict_vals['price_subtotal']
                if 'id' in dict_vals:
                    linies_utilitzades_ids.append(dict_vals['id'])
            elif (tenen_bo_social and dict_vals['product_id']
                  and pbosocial_id == dict_vals['product_id'][0]):
                max_descompte += dict_vals['price_subtotal']
                linies_utilitzades_ids.append(dict_vals['id'])
            elif product_id == dict_vals['product_id'][0]:
                max_descompte += dict_vals['price_subtotal']
                if 'id' in dict_vals:
                    linies_utilitzades_ids.append(dict_vals['id'])
            else:
                # Si tenen IESE, son del sector electric
                impostos_linia = dict_vals['invoice_line_tax_id']
                for impostos_linia_info in self.pool.get("account.tax").read(
                        cursor, uid, impostos_linia, ['name'], context=context
                ):
                    if 'especial' in impostos_linia_info['name'].lower():
                        max_descompte += dict_vals['price_subtotal']
                        if 'id' in dict_vals:
                            linies_utilitzades_ids.append(dict_vals['id'])

        iese_base = iese_quota = iese_amount = 0.0
        iva_base = iva_quota = iva_amount = 0.0
        igic_amount = 0.0
        for line in linia_obj.browse(
                cursor, uid, linies_utilitzades_ids, context={'prefetch': False}
        ):
            if not line.name:  # Si el ID no existeix, al consultar el nom retornara False
                continue

            taxes_dict = {}
            for tax in line.invoice_line_id.invoice_line_tax_id:
                taxes_dict[tax.name] = tax.amount
            has_iese = [v for x, v in taxes_dict.items() if 'especial' in x.lower()]
            has_igic = [v for x, v in taxes_dict.items() if 'igic' in x.lower()]
            other_taxes = [v for x, v in taxes_dict.items() if 'especial' not in x.lower()
                           and 'igic' not in x.lower()]

            if has_iese:
                # We asume there's only one IESE and only one VAT
                iese_base += line.price_subtotal
                iese_quota = has_iese[0]
            if has_igic:
                # We can't asume there'll be only one IGIC so we calculate it here directly
                igic_subtotal = line.price_subtotal * has_igic[0]
                igic_subtotal = round(igic_subtotal, 2)
                igic_amount += igic_subtotal
            if other_taxes:
                # We asume there's only one IESE and only one VAT
                iva_base += line.price_subtotal
                iva_quota = other_taxes[0]

        if iese_base:
            # Let's begin with some weird rounds here, because Python is a bitch and float values
            # are difficult to handle with a precision of 2 decimals. We'll do round 2 after
            # rounding to 6. That's because things like this:
            # round(0.575, 2) = 0.57 BUT:
            # 11.5 * 0.05 = 0.575 (in real maths)
            # round(11.5 * 0.05, 2) = 0.58 !!!!!!!
            # That's because 11.5 * 0.05 in Python is 0.5750000000000001 and it rounds up!!!
            # So we are going to control each and every float rounding to 6 first and then to 2
            # So, doing this round(0.5750000000000001, 6) = 0.575 and round(0.575, 2) = 0.57

            iese_base = uber_round(iese_base)
            if self.has_to_recompute_iese_as_industrial(cursor, uid, factura_id, context=context):
                factor = 0.5
            else:
                factor = 1.0

            fact = fact_obj.browse(cursor, uid, factura_id, context=context)
            linies_energia = self.get_energy_lines_to_count_consume(
                cursor, uid, fact, context=context
            )

            total_energia = 0.0
            for linia in linies_energia:
                total_energia += linia.quantity

            # Mirem si s'ha de fer el mínim segons article 99
            calcul = total_energia / 1000 * factor
            calcul = uber_round(calcul)
            import_iese = uber_round(iese_base * iese_quota)
            import_iese = uber_round(import_iese)
            iese_amount = max(calcul, import_iese)
        if iva_base:
            iva_base = uber_round(iva_base)
            iva_amount = (uber_round(iva_base) + iese_amount) * iva_quota
            iva_amount = uber_round(iva_amount)

        max_descompte += iese_amount + iva_amount + igic_amount
        max_descompte = uber_round(max_descompte)

        return linies_utilitzades_ids, max_descompte


GiscedataFacturacioFacturador()
