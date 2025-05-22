# -*- coding: utf-8 -*-

from osv import osv, fields
import re


class ResPartner(osv.osv):

    _name = "res.partner"
    _inherit = "res.partner"

    def _www_email(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        res = {}
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search_reader(
                cursor, uid, search, ["email"], context={"active_test": False}
            ):
                if addr["email"]:
                    res[partner_id] = addr["email"]
                    break
                else:
                    res[partner_id] = ""
        return res

    def _www_email_inv(self, cursor, uid, ids, name, value, fnct_inv_arg, context=None):
        if isinstance(value, bool) and not value:
            value = None
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search(cursor, uid, search, context={"active_test": False}):
                vals = {"email": value}
                addr_obj.write(cursor, uid, [addr], vals)
                break
        return True

    def _www_street(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        res = {}
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search_reader(
                cursor, uid, search, ["street"], context={"active_test": False}
            ):
                if addr["street"]:
                    res[partner_id] = addr["street"]
                    break
                else:
                    res[partner_id] = ""
        return res

    def _www_street_inv(self, cursor, uid, ids, name, value, fnct_inv_arg, context=None):
        if isinstance(value, bool) and not value:
            value = None
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search(cursor, uid, search, context={"active_test": False}):
                vals = {"nv": value}
                addr_obj.write(cursor, uid, [addr], vals)
                break
        return True

    def _www_zip(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        res = {}
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search_reader(
                cursor, uid, search, ["zip"], context={"active_test": False}
            ):
                if addr["zip"]:
                    res[partner_id] = addr["zip"]
                    break
                else:
                    res[partner_id] = ""
        return res

    def _www_zip_inv(self, cursor, uid, ids, name, value, fnct_inv_arg, context=None):
        if isinstance(value, bool) and not value:
            value = None
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search(cursor, uid, search, context={"active_test": False}):
                vals = {"zip": value}
                addr_obj.write(cursor, uid, [addr], vals)
                break
        return True

    def _www_mobile(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        res = {}
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search_reader(
                cursor, uid, search, ["mobile"], context={"active_test": False}
            ):
                if addr["mobile"]:
                    res[partner_id] = addr["mobile"]
                    break
                else:
                    res[partner_id] = ""
        return res

    def _www_mobile_inv(self, cursor, uid, ids, name, value, fnct_inv_arg, context=None):
        if isinstance(value, bool) and not value:
            value = None
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search(cursor, uid, search):
                vals = {"mobile": value}
                addr_obj.write(cursor, uid, [addr], vals)
                break
        return True

    def _www_phone(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        res = {}
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search_reader(
                cursor, uid, search, ["phone"], context={"active_test": False}
            ):
                if addr["phone"]:
                    res[partner_id] = addr["phone"]
                    break
                else:
                    res[partner_id] = ""
        return res

    def _www_phone_inv(self, cursor, uid, ids, name, value, fnct_inv_arg, context=None):
        if isinstance(value, bool) and not value:
            value = None
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search(cursor, uid, search, context={"active_test": False}):
                vals = {"phone": value}
                addr_obj.write(cursor, uid, [addr], vals)
                break
        return True

    def _www_provincia(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        state_obj = self.pool.get("res.country.state")
        res = {}
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search_reader(
                cursor, uid, search, ["state_id"], context={"active_test": False}
            ):
                if addr["state_id"]:
                    state_name = state_obj.read(cursor, uid, addr["state_id"], ["name"])
                    res[partner_id] = (addr["state_id"], state_name)
                    break
                else:
                    res[partner_id] = ()
        return res

    def _www_provincia_inv(self, cursor, uid, ids, name, value, fnct_inv_arg, context=None):
        if isinstance(value, bool) and not value:
            value = None
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        if not context:
            context = {}

        addr_obj = self.pool.get("res.partner.address")
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search(cursor, uid, search, context={"active_test": False}):
                vals = {"state_id": value}
                addr_obj.write(cursor, uid, [addr], vals)
                break
        return True

    def _www_municipi(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        addr_obj = self.pool.get("res.partner.address")
        municipi_obj = self.pool.get("res.municipi")
        res = {}
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search_reader(
                cursor, uid, search, ["id_municipi"], context={"active_test": False}
            ):
                if addr["id_municipi"]:
                    municipi_name = municipi_obj.read(cursor, uid, addr["id_municipi"], ["name"])
                    res[partner_id] = (addr["id_municipi"], municipi_name)
                    break
                else:
                    res[partner_id] = ()
        return res

    def _www_municipi_inv(self, cursor, uid, ids, name, value, fnct_inv_arg, context=None):
        if isinstance(value, bool) and not value:
            value = None
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        if not context:
            context = {}

        addr_obj = self.pool.get("res.partner.address")
        for partner_id in ids:
            search = [("partner_id.id", "=", partner_id)]
            for addr in addr_obj.search(cursor, uid, search, context={"active_test": False}):
                vals = {"id_municipi": value}
                addr_obj.write(cursor, uid, [addr], vals)
                break
        return True

    def clean_num_soci(self, num_soci):
        return "%s" % int(re.sub("[^0-9]+", "", num_soci))

    def _www_soci(self, cursor, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        partner_obj = self.pool.get("res.partner")
        partner_categ_obj = self.pool.get("res.partner.category")
        search_categ = [("name", "=", "Soci")]
        categs_ids = partner_categ_obj.search(cursor, uid, search_categ)
        if categs_ids and len(categs_ids) > 0:
            soci_category_id = categs_ids[0]
        else:
            soci_category_id = []
        empty_num_soci = "---------"
        read_fields = ["ref", "category_id"]
        res = {}
        for partner_id in ids:
            for soci in partner_obj.read(cursor, uid, [partner_id], read_fields):
                if soci["ref"]:
                    if soci_category_id in soci["category_id"]:
                        res[partner_id] = self.clean_num_soci(soci["ref"])
                    else:
                        res[partner_id] = empty_num_soci
                    break
                else:
                    res[partner_id] = empty_num_soci
        return res

    _columns = {
        "www_email": fields.function(
            _www_email,
            fnct_inv=_www_email_inv,
            string="Email portal",
            size=256,
            type="char",
            method=True,
        ),
        "www_soci": fields.function(
            _www_soci, string="Número de soci", size=256, type="char", method=True
        ),
        "www_street": fields.function(
            _www_street,
            fnct_inv=_www_street_inv,
            string="Carrer portal",
            size=128,
            type="char",
            method=True,
        ),
        "www_zip": fields.function(
            _www_zip, fnct_inv=_www_zip_inv, string="ZIP portal", size=24, type="char", method=True
        ),
        "www_mobile": fields.function(
            _www_mobile,
            fnct_inv=_www_mobile_inv,
            string="Mobile portal",
            size=64,
            type="char",
            method=True,
        ),
        "www_phone": fields.function(
            _www_phone,
            fnct_inv=_www_phone_inv,
            string="Mobile portal",
            size=64,
            type="char",
            method=True,
        ),
        "www_provincia": fields.function(
            _www_provincia,
            fnct_inv=_www_provincia_inv,
            relation="res.country.state",
            string="Provincia portal",
            type="many2one",
            method=True,
        ),
        "www_municipi": fields.function(
            _www_municipi,
            fnct_inv=_www_municipi_inv,
            relation="res.municipi",
            string="Municipi portal",
            type="many2one",
            method=True,
        ),
        "birthdate": fields.date("Data de naixement"),
        "gender": fields.selection(
            [
                ("", ""),
                ("female", "Dona"),
                ("male", "Home"),
                ("gender_fluid", "Gènere fluïd"),
                ("non_binary", "No binària"),
                ("other", "Altres"),
                ("prefer_not_to_say", "Prefereixo no dir-ho"),
            ],
            "Gender"),
    }


ResPartner()
