# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
import mailchimp_marketing as MailchimpMarketing
from tools import config

mail_ningu = "ningu@somenergia.coop"


class WizardSubscribeSociMailchimp(osv.osv_memory):
    """Assistent per subscriure una persona sòcia al Mailchimp"""

    _name = "wizard.subscribe.soci.mailchimp"

    def subscribe_soci_address(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        address_ids = context.get("active_ids", False)
        info_wizard = "S'ha iniciat el procés de subscripció de les adreces següents: \n"

        if not address_ids:
            raise osv.except_osv(u"Error", u"No s'han seleccionat adreces de client")

        address_obj = self.pool.get("res.partner.address")
        soci_obj = self.pool.get("somenergia.soci")
        conf_obj = self.pool.get("res.config")

        list_name = conf_obj.get(cursor, uid, "mailchimp_socis_list", None)

        MAILCHIMP_CLIENT = MailchimpMarketing.Client(
            dict(
                api_key=config.options.get("mailchimp_apikey"),
                server=config.options.get("mailchimp_server_prefix"),
            )
        )
        try:
            list_client_id = address_obj.get_mailchimp_list_id(list_name, MAILCHIMP_CLIENT)
        except Exception as e:
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
                soci_data = address_obj.fill_merge_fields_soci(cursor, uid, address)
                address_obj.subscribe_mail_in_list(
                    cursor, uid, [soci_data], list_client_id, MAILCHIMP_CLIENT
                )

                info_wizard += address_data["email"] + "\n"

        self.write(cursor, uid, ids, {"info": info_wizard, "state": "end"}, context=context)

    _columns = {
        "info": fields.text("Info"),
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
    }

    _defaults = {
        "info": _(u'Aquest assitent subscriu el Soci a la llista de Mailchimp de "Socis"'),
        "state": lambda *a: "init",
    }


WizardSubscribeSociMailchimp()
