# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction

from expects import expect, contain, be_false, equal, be_true, be_empty
import osv


class EnergeticaTests(testing.OOTestCase):
    def set_soci(self, cursor, uid, contract_id, soci_id=None):
        if soci_id is None:
            imd_obj = self.openerp.pool.get("ir.model.data")
            soci_id = imd_obj.get_object_reference(
                cursor, uid, "som_energetica", "res_partner_energetica"
            )[1]

        contract_obj = self.openerp.pool.get("giscedata.polissa")
        contract_obj.write(cursor, uid, contract_id, {"soci": soci_id})

    def test_is_energetica(self):
        contract_obj = self.openerp.pool.get("giscedata.polissa")
        product_obj = self.openerp.pool.get("product.product")
        imd_obj = self.openerp.pool.get("ir.model.data")
        facturador_obj = self.openerp.pool.get("giscedata.facturacio.facturador")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            energetica_soci_id = imd_obj.get_object_reference(
                cursor, uid, "som_energetica", "res_partner_energetica"
            )[1]

            contract_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )[1]

            # No soci
            res = contract_obj.is_energetica(cursor, uid, contract_id)
            expect(res).to(be_false)

            # soci no energética
            self.set_soci(cursor, uid, contract_id, 1)
            res = contract_obj.is_energetica(cursor, uid, contract_id)
            dona_id = facturador_obj.get_donatiu_product(cursor, uid, contract_id)
            prod_data = product_obj.read(cursor, uid, dona_id, ["default_code"])

            expect(res).to(be_false)
            expect(prod_data["default_code"]).to(equal("DN01"))

            # soci energética
            self.set_soci(cursor, uid, contract_id, energetica_soci_id)
            res = contract_obj.is_energetica(cursor, uid, contract_id)
            dona_id = facturador_obj.get_donatiu_product(cursor, uid, contract_id)
            prod_data = product_obj.read(cursor, uid, dona_id, ["default_code"])

            expect(res).to(be_true)
            expect(prod_data["default_code"]).to(equal("DN02"))

    def test_is_candela(self):
        contract_obj = self.openerp.pool.get("giscedata.polissa")
        imd_obj = self.openerp.pool.get("ir.model.data")
        rp_obj = self.openerp.pool.get("res.partner")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            candela_soci_id = rp_obj.search(
                cursor, uid, [("ref", "=", "S076331")], limit=1
            )[0]

            contract_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )[1]

            # No soci
            res = contract_obj.is_candela(cursor, uid, contract_id)
            expect(res).to(be_false)

            # soci no Candela
            self.set_soci(cursor, uid, contract_id, 1)
            res = contract_obj.is_candela(cursor, uid, contract_id)
            expect(res).to(be_false)

            # soci Candela
            self.set_soci(cursor, uid, contract_id, candela_soci_id)
            res = contract_obj.is_candela(cursor, uid, contract_id)
            expect(res).to(be_true)

    def test_bad_energetica_partners(self):
        contract_obj = self.openerp.pool.get("giscedata.polissa")
        imd_obj = self.openerp.pool.get("ir.model.data")

        for field in "titular", "pagador", "altre_p":
            with Transaction().start(self.database) as txn:
                cursor = txn.cursor
                uid = txn.user

                cat_energetica_id = imd_obj.get_object_reference(
                    cursor, uid, "som_energetica", "res_partner_category_energetica"
                )[1]

                contract_id = imd_obj.get_object_reference(
                    cursor, uid, "giscedata_polissa", "polissa_0001"
                )[1]

                self.set_soci(cursor, uid, contract_id)

                contract = contract_obj.browse(cursor, uid, contract_id)
                field_object = getattr(contract, field)
                if not field_object:
                    continue
                if isinstance(field_object, osv.orm.browse_null):
                    continue
                field_object.write({"category_id": [(6, 0, [cat_energetica_id])]})

                partners_ids = contract_obj.get_bad_energetica_partners(cursor, uid, contract_id)

                expect(partners_ids).to_not(contain(field_object.id))

    def test_bad_energetica_partners_full(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            contract_obj = self.openerp.pool.get("giscedata.polissa")
            partner_obj = self.openerp.pool.get("res.partner")
            address_obj = self.openerp.pool.get("res.partner.address")
            bank_obj = self.openerp.pool.get("res.partner.bank")
            imd_obj = self.openerp.pool.get("ir.model.data")

            imd_obj.get_object_reference(
                cursor, uid, "som_energetica", "res_partner_category_energetica"
            )[1]

            contract_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )[1]

            partner_ids = partner_obj.search(cursor, uid, [])
            bank_ids = bank_obj.search(cursor, uid, [])
            address_ids = address_obj.search(cursor, uid, [])
            contract_obj.write(
                cursor,
                uid,
                contract_id,
                {
                    "titular": partner_ids[-1],
                    "pagador": partner_ids[-2],
                    "altre_p": partner_ids[-3],
                    "administradora": partner_ids[-4],
                    "bank": bank_ids[-1],
                    "direccio_pagament": address_ids[-1],
                    "direccio_notificacio": address_ids[-2],
                },
            )
            address_obj.write(cursor, uid, address_ids[-1], {"partner_id": partner_ids[-5]})
            address_obj.write(cursor, uid, address_ids[-2], {"partner_id": partner_ids[-6]})
            bank_obj.write(cursor, uid, bank_ids[-1], {"partner_id": partner_ids[-7]})

            bad_ids = contract_obj.get_bad_energetica_partners(cursor, uid, contract_id)
            expect(bad_ids).to(be_empty)

            self.set_soci(cursor, uid, contract_id)

            bad_ids = contract_obj.get_bad_energetica_partners(cursor, uid, contract_id)
            expect(set(bad_ids)).to(equal(set(partner_ids[-7:])))

    def test_bad_energetica_partners_one(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            contract_obj = self.openerp.pool.get("giscedata.polissa")
            partner_obj = self.openerp.pool.get("res.partner")
            address_obj = self.openerp.pool.get("res.partner.address")
            bank_obj = self.openerp.pool.get("res.partner.bank")
            imd_obj = self.openerp.pool.get("ir.model.data")

            imd_obj.get_object_reference(
                cursor, uid, "som_energetica", "res_partner_category_energetica"
            )[1]

            contract_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )[1]

            partner_ids = partner_obj.search(cursor, uid, [])
            bank_ids = bank_obj.search(cursor, uid, [])
            address_ids = address_obj.search(cursor, uid, [])
            contract_obj.write(
                cursor,
                uid,
                contract_id,
                {
                    "titular": partner_ids[-1],
                    "pagador": partner_ids[-1],
                    "altre_p": partner_ids[-1],
                    "administradora": partner_ids[-1],
                    "bank": bank_ids[-1],
                    "direccio_pagament": address_ids[-1],
                    "direccio_notificacio": address_ids[-2],
                },
            )
            address_obj.write(cursor, uid, address_ids[-1], {"partner_id": partner_ids[-1]})
            address_obj.write(cursor, uid, address_ids[-2], {"partner_id": partner_ids[-1]})
            bank_obj.write(cursor, uid, bank_ids[-1], {"partner_id": partner_ids[-1]})

            bad_ids = contract_obj.get_bad_energetica_partners(cursor, uid, contract_id)
            expect(bad_ids).to(be_empty)

            self.set_soci(cursor, uid, contract_id)

            bad_ids = contract_obj.get_bad_energetica_partners(cursor, uid, contract_id)
            expect(set(bad_ids)).to(equal(set(partner_ids[-1:])))

    def test_set_energetica(self):
        contract_obj = self.openerp.pool.get("giscedata.polissa")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            contract_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )[1]

            self.set_soci(cursor, uid, contract_id)
            # not set
            partners_ids = contract_obj.get_bad_energetica_partners(cursor, uid, contract_id)

            expect(partners_ids).to_not(be_empty)

            contract_obj.set_energetica(cursor, uid, contract_id)

            # energetica setted
            partners_ids = contract_obj.get_bad_energetica_partners(cursor, uid, contract_id)
            expect(partners_ids).to(be_empty)

    def test_create_contract_soci_energetica(self):
        contract_obj = self.openerp.pool.get("giscedata.polissa")
        partner_obj = self.openerp.pool.get("res.partner")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            _, self.demo_contract_01 = imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )
            cat_energetica_id = imd_obj.get_object_reference(
                cursor, uid, "som_energetica", "res_partner_category_energetica"
            )[1]

            vals, _ = contract_obj.copy_data(cursor, uid, self.demo_contract_01)

            soci_id = imd_obj.get_object_reference(
                cursor, uid, "som_energetica", "res_partner_energetica"
            )[1]

            vals.update({"soci": soci_id})

            new_contract_id = contract_obj.create(cursor, uid, vals)

            # energetica setted
            partners_ids = contract_obj.get_bad_energetica_partners(cursor, uid, new_contract_id)
            expect(partners_ids).to(be_empty)

            par_ids = self.get_all_partners(cursor, uid, new_contract_id)
            for par_id in par_ids:
                partner_data = partner_obj.read(cursor, uid, par_id)
                expect(partner_data["category_id"]).to(contain(cat_energetica_id))

    def test_create_contract_no_soci_energetica(self):
        contract_obj = self.openerp.pool.get("giscedata.polissa")
        partner_obj = self.openerp.pool.get("res.partner")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            _, self.demo_contract_01 = imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )
            cat_energetica_id = imd_obj.get_object_reference(
                cursor, uid, "som_energetica", "res_partner_category_energetica"
            )[1]

            vals, _ = contract_obj.copy_data(cursor, uid, self.demo_contract_01)

            new_contract_id = contract_obj.create(cursor, uid, vals)

            # energetica setted
            partners_ids = contract_obj.get_bad_energetica_partners(cursor, uid, new_contract_id)
            expect(partners_ids).to(be_empty)

            par_ids = self.get_all_partners(cursor, uid, new_contract_id)
            for par_id in par_ids:
                partner_data = partner_obj.read(cursor, uid, par_id)
                expect(partner_data["category_id"]).not_to(contain(cat_energetica_id))

    def get_all_partners(self, cursor, uid, contract_id):
        contract_fields = ["titular", "pagador", "altre_p", "administradora"]
        contract_obj = self.openerp.pool.get("giscedata.polissa")
        contract_data = contract_obj.read(cursor, uid, contract_id, contract_fields)

        partners_list = []
        for contract_field in contract_fields:
            if not contract_data[contract_field]:
                continue
            partner_id = contract_data[contract_field][0]
            partners_list.append(partner_id)

        contract = contract_obj.browse(cursor, uid, contract_id)

        if contract.bank and contract.bank.partner_id:
            partners_list.append(contract.bank.partner_id.id)

        if contract.direccio_pagament and contract.direccio_pagament.partner_id:
            partners_list.append(contract.direccio_pagament.partner_id.id)

        if contract.direccio_notificacio and contract.direccio_notificacio.partner_id:
            partners_list.append(contract.direccio_notificacio.partner_id.id)

        return list(set(partners_list))

    def test_get_donatiu_product_som_energia(self):
        facturador_obj = self.openerp.pool.get("giscedata.facturacio.facturador")
        product_obj = self.openerp.pool.get("product.product")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            contract_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )[1]

            dona_id = facturador_obj.get_donatiu_product(cursor, uid, contract_id)

            prod_data = product_obj.read(cursor, uid, dona_id, ["default_code"])
            expect(prod_data["default_code"]).to(equal("DN01"))

    def test_get_donatiu_product_energetica(self):
        facturador_obj = self.openerp.pool.get("giscedata.facturacio.facturador")
        product_obj = self.openerp.pool.get("product.product")
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            contract_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )[1]
            energetica_id = imd_obj.get_object_reference(
                cursor, uid, "som_energetica", "res_partner_energetica"
            )[1]
            pol_obj.write(cursor, uid, contract_id, {"soci": energetica_id})

            dona_id = facturador_obj.get_donatiu_product(cursor, uid, contract_id)

            prod_data = product_obj.read(cursor, uid, dona_id, ["default_code"])
            expect(prod_data["default_code"]).to(equal("DN02"))

    def test_get_donatiu_product_candela(self):
        facturador_obj = self.openerp.pool.get("giscedata.facturacio.facturador")
        product_obj = self.openerp.pool.get("product.product")
        rp_obj = self.openerp.pool.get("res.partner")
        imd_obj = self.openerp.pool.get("ir.model.data")
        pol_obj = self.openerp.pool.get("giscedata.polissa")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            contract_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_polissa", "polissa_0001"
            )[1]
            candela_id = rp_obj.search(
                cursor, uid, [("ref", "=", "S076331")], limit=1
            )[0]
            pol_obj.write(cursor, uid, contract_id, {"soci": candela_id})

            dona_id = facturador_obj.get_donatiu_product(cursor, uid, contract_id)

            prod_data = product_obj.read(cursor, uid, dona_id, ["default_code"])
            expect(prod_data["default_code"]).to(equal("DN03"))
