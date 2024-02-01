# -*- coding: utf-8 -*-
from datetime import datetime
from osv import osv, fields
from osv.osv import except_osv


class ResPartner(osv.osv):
    """ResPartner amb categoria i seqüencia d'administrador de pòlisses"""

    _name = "res.partner"
    _inherit = "res.partner"

    def create_contract_administrator(self, cursor, uid, data, context=None):
        """
        data is a dictionary with the following items:
            - name: comma separated partner's name (e.g: "Testing, Persona"),
            - vat: partner's VAT (e.g: "ES12345678Z"),
            - lang: partner's lang (e.g: "ca_ES"),
            - email: partner's email address (e.g: "test@test.coop"),
            - comment: comment visible from partner's file,
            - comercial: commercial's name (e.g: "webforms")
        """
        if context is None:
            context = {}
        vat = data.get("vat", "")

        if not vat:
            raise except_osv("Error", "El camp VAT no té valor")

        partner_ids = self.search(cursor, uid, [("vat", "=", vat)])
        if partner_ids:
            raise except_osv("Error", "El partner ja existeix")

        ir_seq = self.pool.get("ir.sequence")
        padress_obj = self.pool.get("res.partner.address")

        now = datetime.now()
        partner_vals = {
            "name": data.get("name", ""),
            "vat": vat,
            "ref": ir_seq.get_next(cursor, uid, "res.partner.administradora"),
            "active": True,
            "lang": data.get("lang", ""),
            "comment": data.get("comment", ""),
            "comercial": data.get("comercial", ""),
            "date": now.strftime("%Y-%m-%d"),
            "customer": True,
        }

        partner_id = self.create(cursor, uid, partner_vals, context)

        self.add_administrator_category(cursor, uid, partner_id, context=None)

        partner = self.read(cursor, uid, partner_id, ["name", "ref"])

        # Assign res.partner.address
        partner_address_vals = {
            "partner_id": partner_id,
            "name": partner["name"],
            "email": data.get("email", ""),
        }
        padress_obj.create(cursor, uid, partner_address_vals, context)

        return partner_id

    def add_administrator_category(self, cursor, uid, partner_ids, context=None):
        if type(partner_ids) not in (list, tuple):
            partner_ids = [partner_ids]

        imd_obj = self.pool.get("ir.model.data")
        admin_cat = imd_obj._get_obj(
            cursor, uid, "som_polissa_administradora", "res_partner_category_administradora"
        )

        for partner_id in partner_ids:
            partner = self.read(cursor, uid, partner_id, ["category_id"])
            if admin_cat.id not in partner["category_id"]:
                self.write(cursor, uid, partner_id, {"category_id": [(4, admin_cat.id)]})

    def become_owner(self, cursor, uid, id, context=None):
        imd_obj = self.pool.get("ir.model.data")
        ir_seq = self.pool.get("ir.sequence")
        soci_cat = imd_obj._get_obj(cursor, uid, "som_partner_account", "res_partner_category_soci")
        partner = self.read(cursor, uid, id, ["ref", "category_id"])

        # Assign Owner ref code
        if soci_cat.id in partner["category_id"]:
            raise except_osv("Error", "No es pot passar de soci a titular")
        elif partner["ref"][0] != "T":
            codi = ir_seq.get(cursor, uid, "res.partner.titular")
            self.write(cursor, uid, id, {"ref": codi})


ResPartner()
