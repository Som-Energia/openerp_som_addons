# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


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
        self.pool.get("res.config")

        MAILCHIMP_CLIENT = address_obj._get_mailchimp_client()
        list_names = self._get_members_mailchimp_lists(cursor, uid, ids, context=context)

        try:
            list_ids = [self.get_mailchimp_list_id(name, MAILCHIMP_CLIENT) for name in list_names]
        except Exception as e:
            raise osv.except_osv(u"Error", str(e))

        for address in address_ids:
            address_data = address_obj.read(cursor, uid, address, ["email", "partner_id"])
            if not address_data["email"]:
                raise osv.except_osv(u"Error", u"L'adreça seleccionada no té email")

            is_member = soci_obj.search(
                cursor,
                uid,
                [("partner_id", "=", address_data["partner_id"][0]), ("baixa", "=", False)],
            )
            if is_member:
                soci_data = address_obj.fill_merge_fields_soci(cursor, uid, address)
                for list_client_id in list_ids:
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
