# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
import mailchimp_marketing as MailchimpMarketing
from tools import config

mail_ningu = "ningu@somenergia.coop"


class WizardSubscribeClientMailchimp(osv.osv_memory):
    """Assistent per subscriure una persona clienta no sòcia al Mailchimp"""

    _name = "wizard.subscribe.client.mailchimp"

    def subscribe_client_address(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        address_ids = context.get("active_ids", False)
        info_wizard = "S'ha iniciat el procés de subscripció de les adreces següents: \n"

        if not address_ids:
            raise osv.except_osv(u"Error", u"No s'han seleccionat adreces de client")

        address_obj = self.pool.get("res.partner.address")
        soci_obj = self.pool.get("somenergia.soci")
        conf_obj = self.pool.get("res.config")

        list_name = conf_obj.get(cursor, uid, "mailchimp_clients_list", None)

        MAILCHIMP_CLIENT = MailchimpMarketing.Client(
            dict(
                api_key=config.options.get("mailchimp_apikey"),
                server=config.options.get("mailchimp_server_prefix"),
            )
        )
        try:
            list_client_id = address_obj.get_mailchimp_list_id(list_name, MAILCHIMP_CLIENT)
        except Exception as e:
            # import pudb;pu.db
            raise osv.except_osv(u"Error", str(e))

        for address in address_ids:
            address_data = address_obj.read(cursor, uid, address, ["email", "partner_id"])
            if not address_data["email"]:
                raise osv.except_osv(u"Error", u"L'adreça seleccionada no té email")
            if address_data["email"] == mail_ningu:
                continue

            is_member = soci_obj.search(
                cursor,
                uid,
                [("partner_id", "=", address_data["partner_id"][0]), ("baixa", "=", False)],
            )
            if is_member:
                pass
            else:
                client_data = address_obj.fill_merge_fields_clients(cursor, uid, address)
                address_obj.subscribe_mail_in_list(
                    cursor, uid, [client_data], list_client_id, MAILCHIMP_CLIENT
                )

                info_wizard += address_data["email"] + "\n"

        self.write(cursor, uid, ids, {"info": info_wizard, "state": "end"}, context=context)

    _columns = {
        "info": fields.text("Info"),
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
    }

    _defaults = {
        "info": _(
            u'Aquest assitent subscriu el Client a la llista de Mailchimp de "Clients No Socis"'
        ),
        "state": lambda *a: "init",
    }


WizardSubscribeClientMailchimp()
