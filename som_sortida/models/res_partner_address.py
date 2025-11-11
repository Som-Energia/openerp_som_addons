# -*- coding: utf-8 -*-

from osv import osv

FIELDS_CTSS = {
    "email": "EMAIL",
    "Nom": "FNAME",
    "Cognoms": "LNAME",
    "Idioma": "MMERGE3",
    "Origen": "MMERGE4",  # "Origen vinculat al CT sense socia"
    "num_socia": "MMERGE5",
    "situacio_socia": "MMERGE6",  # Apadrinada or Socia propia
    "Municipi": "MMERGE7",
    "Comarca": "MMERGE8",
    "provincia": "MMERGE9",
    "comunitat_autonoma": "MMERGE10",
    "codi_postal": "MMERGE11",
}


class ResPartnerAddress(osv.osv):
    """
    Class to manage Mailchimp lists subscriptions
    This is the only class that should connect to Mailchimp API
    """

    _inherit = "res.partner.address"

    def subscribe_polissa_titular_in_ctss_lists(self, cursor, uid, polissa_ids, context=None):
        if not isinstance(polissa_ids, (list, tuple)):
            polissa_ids = [polissa_ids]

        MAILCHIMP_CLIENT = self._get_mailchimp_client()
        conf_obj = self.pool.get("res.config")
        list_name = conf_obj.get(cursor, uid, "mailchimp_clients_ctss_list", None)
        list_id = self.get_mailchimp_list_id(list_name, MAILCHIMP_CLIENT)
        for _id in polissa_ids:
            client_data = self.fill_merge_fields_titular_polissa_ctss(cursor, uid, _id)
            self.subscribe_mail_in_list_async(
                cursor, uid, [client_data], list_id, MAILCHIMP_CLIENT
            )

    def update_polissa_titular_in_ctss_lists(self, cursor, uid, polissa_ids, context=None):
        if not isinstance(polissa_ids, (list, tuple)):
            polissa_ids = [polissa_ids]
        conf_obj = self.pool.get("res.config")
        list_name = conf_obj.get(cursor, uid, "mailchimp_clients_ctss_list", None)
        for _id in polissa_ids:
            client_data = self.fill_merge_fields_titular_polissa_ctss(cursor, uid, _id)
            self.update_or_create_data_in_list_mailchimp_async(
                cursor, uid, [client_data], [list_name], context
            )

    def _get_polissa_data(self, cursor, uid, polissa_id, context=None):
        pol_obj = self.pool.get("giscedata.polissa")
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)
        polissa_data = {
            "num_socia": polissa.soci.ref,
            "situacio_socia": "Apadrinada" if polissa.soci.id != polissa.titular.id else "Socia propia",  # noqa: E501
            "category_id": [cat.id for cat in polissa.category_id or []],
        }
        return polissa_data

    def fill_merge_fields_titular_polissa_ctss(self, cursor, uid, polissa_id, context=None):
        if isinstance(polissa_id, (list, tuple)):
            polissa_id = polissa_id[0]
        partner_obj = self.pool.get("res.partner")
        municipi_obj = self.pool.get("res.municipi")
        pol_obj = self.pool.get("giscedata.polissa")
        polissa = pol_obj.browse(cursor, uid, polissa_id, context=context)
        partner_data = self.read(
            cursor, uid, polissa.titular.address[0].id, [
                "partner_id", "email", "zip", "id_municipi", "mobile", "phone"]
        )
        partner_fields = partner_obj.read(
            cursor, uid, partner_data["partner_id"][0], ["name", "lang", "vat", "ref"]
        )
        pol_data = self._get_polissa_data(cursor, uid, polissa_id, context=context)
        empresa = self._es_empresa(cursor, uid, pol_data, context)
        nom_pila = self._get_nom_pila(cursor, uid, partner_data["partner_id"][0], partner_fields, empresa, context)  # noqa: E501
        mailchimp_member = {
            "email_address": partner_data["email"],
            "status": "subscribed",
            "merge_fields": {
                FIELDS_CTSS["email"]: partner_data["email"],
                FIELDS_CTSS["Nom"]: nom_pila,
                FIELDS_CTSS["Idioma"]: partner_fields["lang"],
                FIELDS_CTSS["Origen"]: "Origen vinculat al CT sense socia",
                # FIELDS_CTSS["Cognoms_Nom"]: partner_fields["name"],
                FIELDS_CTSS["num_socia"]: pol_data["num_socia"],  # ojo, obtenir de polissa
                # TODO: obtenir de polissa
                FIELDS_CTSS["situacio_socia"]: pol_data['situacio_socia'],
                FIELDS_CTSS["codi_postal"]: partner_data["zip"],
            },
        }

        if partner_data["id_municipi"]:
            municipi_data = municipi_obj.browse(cursor, uid, partner_data["id_municipi"][0])
            comarca_name = ""
            if municipi_data.comarca:
                comarca_name = municipi_data.comarca.name
            provincia_name = municipi_data.state.name
            ccaa_name = municipi_data.state.comunitat_autonoma.name
            mailchimp_member["merge_fields"].update(
                {
                    FIELDS_CTSS["provincia"]: provincia_name,
                    FIELDS_CTSS["comunitat_autonoma"]: ccaa_name,
                    FIELDS_CTSS["Comarca"]: comarca_name,
                    FIELDS_CTSS["Municipi"]: municipi_data.name,
                }
            )

        return mailchimp_member


ResPartnerAddress()
