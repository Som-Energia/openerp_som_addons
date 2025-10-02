# -*- coding: utf-8 -*-
from osv import osv
from oorq.decorators import job


class ResPartner(osv.osv):
    """Class to manage Mailchimp lists subscriptions"""

    _name = "res.partner"
    _inherit = "res.partner"

    @job(queue="mailchimp_tasks")
    def arxiva_client_mailchimp_async(self, cursor, uid, ids, context=None):
        """
        Archive member async method
        """
        return self.arxiva_client_mailchimp(cursor, uid, ids, context=context)

    def arxiva_client_mailchimp(self, cursor, uid, ids, context=None):
        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        res_partner_obj = self.pool.get("res.partner")
        soci_obj = self.pool.get("somenergia.soci")
        conf_obj = self.pool.get("res.config")
        res_partner_address_obj = self.pool.get("res.partner.address")

        is_member = soci_obj.search(cursor, uid, [("partner_id", "=", ids), ("baixa", "=", False)])
        if is_member:
            return

        MAILCHIMP_CLIENT = res_partner_address_obj._get_mailchimp_client()
        list_name = conf_obj.get(cursor, uid, "mailchimp_clients_list", None)

        list_id = res_partner_address_obj.get_mailchimp_list_id(list_name, MAILCHIMP_CLIENT)

        address_list = res_partner_obj.read(cursor, uid, ids, ["address"])["address"]
        res_partner_address_obj.archieve_mail_in_list(
            cursor, uid, address_list, list_id, MAILCHIMP_CLIENT
        )

    @job(queue="mailchimp_tasks")
    def subscribe_client_mailchimp_async(self, cursor, uid, ids, context=None):
        """
        Archive member async method
        """
        return self.subscribe_client_mailchimp(cursor, uid, ids, context=context)

    def subscribe_client_mailchimp(self, cursor, uid, ids, context=None):
        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        res_partner_obj = self.pool.get("res.partner")
        soci_obj = self.pool.get("somenergia.soci")
        res_partner_address_obj = self.pool.get("res.partner.address")
        conf_obj = self.pool.get("res.config")

        is_member = soci_obj.search(cursor, uid, [("partner_id", "=", ids), ("baixa", "=", False)])
        if not is_member:
            return
        MAILCHIMP_CLIENT = res_partner_address_obj._get_mailchimp_client()
        list_name = conf_obj.get(cursor, uid, "mailchimp_clients_list", None)

        list_id = res_partner_address_obj.get_mailchimp_list_id(list_name, MAILCHIMP_CLIENT)

        address_list = res_partner_obj.read(cursor, uid, ids, ["address"])["address"]
        res_partner_address_obj.subscribe_mail_in_list(
            cursor, uid, address_list, list_id, MAILCHIMP_CLIENT
        )


ResPartner()
