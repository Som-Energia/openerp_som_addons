# -*- coding: utf-8 -*-

from osv import osv
from tools.translate import _

import logging
from hashlib import md5
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
from oorq.decorators import job
from tools import config

FIELDS_NO_MEMBERS = {
    "zip_code": "MMERGE10",
    "province": "MMERGE7",
    "region": "MMERGE8",
    "name": "MMERGE9",
    "comarca": "MMERGE6",
    "municipality": "MMERGE5",
    "member_num": "MMERGE4",
    "lang": "MMERGE3",
    "surname": "LNAME",
    "firstname": "FNAME",
    "email": "EMAIL",
}

FIELDS_SOCIS = {
    "Cognoms, nom": "MMERGE5",
    "NumSoci": "MMERGE4",
    "E-mail": "EMAIL",
    "Categoria": "MMERGE2",
    "Ciutat": "MMERGE3",
    "Provincia": "MMERGE6",
    "CodiPostal": "MMERGE7",
    "Idioma": "MMERGE8",
    "Empresa": "MMERGE9",
    "Telefon": "MMERGE10",  # (###)###-####
    "Comarca": "MMERGE11",
    "NIF": "MMERGE1",
    "comunitat_autonoma": "MMERGE13",
    "Enllac": "MMERGE12",
    "Generation": "MMERGE14",
    "No rebre condicions generals": "MMERGE15",
    "Assamblea Virtual": "MMERGE16",
    "Nom empresa": "MMERGE17",
    "Proj. Transicio Energet": "MMERGE18",
    "Compra Coletiva": "MMERGE19",
}


class ResPartnerAddress(osv.osv):
    """Class to manage Mailchimp lists subscriptions"""

    _name = "res.partner.address"
    _inherit = "res.partner.address"

    def _get_mailchimp_client(self):
        return MailchimpMarketing.Client(
            dict(
                api_key=config.options.get("mailchimp_apikey"),
                server=config.options.get("mailchimp_server_prefix"),
            )
        )

    def write(self, cursor, uid, ids, vals, context=None):
        """ Override write to detect email changes and update Mailchimp """
        if context is None:
            context = {}

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        MAILCHIMP_CLIENT = self._get_mailchimp_client()
        if "email" in vals:
            for _id in ids:
                old_email = self.read(cursor, uid, _id, ["email"])["email"]
                email = vals["email"]
                if not old_email or old_email == email:
                    continue

                if not email:
                    self.unsubscribe_client_email_in_all_lists_async(
                        cursor, uid, _id, old_email, MAILCHIMP_CLIENT
                    )
                else:
                    self.update_client_email_in_all_lists_async(
                        cursor, uid, _id, old_email, email, MAILCHIMP_CLIENT
                    )

        return super(ResPartnerAddress, self).write(cursor, uid, ids, vals, context=context)

    @staticmethod
    def get_mailchimp_list_id(list_name, mailchip_conn):
        all_lists = mailchip_conn.lists.get_all_lists(fields=["lists.id,lists.name"], count=100)[
            "lists"
        ]

        for lis in all_lists:
            if lis["name"] == list_name:
                return lis["id"]
        raise osv.except_osv(_("Error"), _("List: <{}> not found".format(list_name)))

    @job(queue="mailchimp_tasks")
    def archieve_mail_in_list(self, cursor, uid, ids, list_id, mailchimp_conn, context=None):
        self.archieve_mail_in_list_sync(cursor, uid, ids, list_id, mailchimp_conn, context=None)

    def archieve_mail_in_list_sync(self, cursor, uid, ids, list_id, mailchimp_conn, context=None):
        """
        Archive an email in a Mailchimp list
        """
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        logger = logging.getLogger("openerp.{0}.archieve_mail_in_list".format(__name__))

        email_addresses = self.read(cursor, uid, ids, ["email"])
        for email in email_addresses:
            subscriber_hash = md5(email["email"].lower()).hexdigest()
            try:
                mailchimp_conn.lists.delete_list_member(
                    list_id=list_id, subscriber_hash=subscriber_hash
                )
            except ApiClientError as error:
                if error.status_code == 404:
                    logger.warning(
                        "L'API no ha permès arxivar l'email {}. "
                        "Error comú quan el mail no es troba a la llista: "
                        "Error de l'API: {}".format(email, error.text)
                    )
                elif error.status_code == 405:
                    logger.warning(
                        "L'API no ha permès arxivar l'email {}. "
                        "Error comú quan el mail ja ha estat arxivat de la llista: "
                        "Error de l'API: {}".format(email, error.text)
                    )
                else:
                    raise osv.except_osv(
                        _("Error"), _("Error archieving email {}:\n{}".format(email, error.text))
                    )
            else:
                logger.info("Email arxivat: {}".format(email))

    def fill_merge_fields_clients(self, cursor, uid, id, context=None):
        """
        Prepare the fields with the data of a non-member client, to be sent to Mailchimp
        """
        partner_obj = self.pool.get("res.partner")
        municipi_obj = self.pool.get("res.municipi")
        self.pool.get("res.comunitat.autonoma")
        partner_data = self.read(cursor, uid, id, ["partner_id", "email", "zip", "id_municipi"])
        partner_fields = partner_obj.read(
            cursor, uid, partner_data["partner_id"][0], ["name", "lang"]
        )

        mailchimp_member = {
            "email_address": partner_data["email"],
            "status": "subscribed",
            "merge_fields": {
                FIELDS_NO_MEMBERS["name"]: partner_fields["name"],
                FIELDS_NO_MEMBERS["lang"]: partner_fields["lang"],
                FIELDS_NO_MEMBERS["surname"]: partner_fields["name"].split(",")[0],
                FIELDS_NO_MEMBERS["firstname"]: partner_fields["name"].split(",")[-1],
                FIELDS_NO_MEMBERS["email"]: partner_data["email"],
                FIELDS_NO_MEMBERS["zip_code"]: partner_data["zip"],
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
                    FIELDS_NO_MEMBERS["province"]: provincia_name,
                    FIELDS_NO_MEMBERS["region"]: ccaa_name,
                    FIELDS_NO_MEMBERS["comarca"]: comarca_name,
                    FIELDS_NO_MEMBERS["municipality"]: municipi_data.name,
                }
            )

        return mailchimp_member

    def fill_merge_fields_soci(self, cursor, uid, id, context=None):
        """
        Prepare the fields with the data of a member, to be sent to Mailchimp
        """
        partner_obj = self.pool.get("res.partner")
        municipi_obj = self.pool.get("res.municipi")
        self.pool.get("res.comunitat.autonoma")
        partner_data = self.read(
            cursor, uid, id, ["partner_id", "email", "zip", "id_municipi", "mobile", "phone"]
        )
        partner_fields = partner_obj.read(
            cursor, uid, partner_data["partner_id"][0], ["name", "lang", "vat", "ref"]
        )

        mailchimp_member = {
            "email_address": partner_data["email"],
            "status": "subscribed",
            "merge_fields": {
                FIELDS_SOCIS["Cognoms, nom"]: partner_fields["name"],
                FIELDS_SOCIS["Idioma"]: partner_fields["lang"],
                FIELDS_SOCIS["E-mail"]: partner_data["email"],
                FIELDS_SOCIS["CodiPostal"]: partner_data["zip"],
                FIELDS_SOCIS["NIF"]: partner_fields["vat"],
                FIELDS_SOCIS["NumSoci"]: partner_fields["ref"],
                FIELDS_SOCIS["Telefon"]: partner_data["phone"]
                if partner_data["phone"]
                else partner_data["mobile"],
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
                    FIELDS_SOCIS["Provincia"]: provincia_name,
                    FIELDS_SOCIS["comunitat_autonoma"]: ccaa_name,
                    FIELDS_SOCIS["Comarca"]: comarca_name,
                    FIELDS_SOCIS["Ciutat"]: municipi_data.name,
                }
            )

        return mailchimp_member

    @job(queue="mailchimp_tasks")
    def subscribe_mail_in_list(
        self, cursor, uid, clients_data, list_id, mailchimp_conn, context=None
    ):
        """ Subscribe a list of clients to a Mailchimp list """
        logger = logging.getLogger("openerp.{0}.subscribe_mail_in_list".format(__name__))
        for client_data in clients_data:
            try:
                mailchimp_conn.lists.add_list_member(list_id, client_data)
            except ApiClientError as e:
                if e.status_code == 400 and e.text.title == "Member Exists":
                    logger.warning(
                        "El correu {} que intentem subscriure ja esta subscrit."
                        "Error de l'API: {}".format(client_data["email_address"], e.text)
                    )
                else:
                    raise osv.except_osv(
                        _("Error"),
                        _(
                            "Error en subscriure l'email {}:\n{}".format(
                                client_data["email_address"], e.text
                            )
                        ),
                    )

    @job(queue="mailchimp_tasks")
    def update_client_email_in_all_lists_async(
        self, cursor, uid, ids, old_email, email, mailchimp_conn, context=None
    ):
        self.update_client_email_in_all_lists(
            cursor, uid, ids, old_email, email, mailchimp_conn, context=None
        )

    def update_client_email_in_all_lists(
        self, cursor, uid, ids, old_email, email, mailchimp_conn, context=None
    ):
        ''' Update email of a client in all Mailchimp lists where it is subscribed '''
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        logger = logging.getLogger("openerp.{0}.update_client_email_in_all_lists".format(__name__))

        all_lists = mailchimp_conn.lists.get_all_lists(
            fields=["lists.id,lists.name"], count=100, email=old_email
        )["lists"]

        for _id in ids:
            for mchimp_list in all_lists:
                list_id = mchimp_list["id"]
                subscriber_hash = md5(old_email.lower()).hexdigest()
                new_subscriber_hash = md5(email.lower()).hexdigest()

                try:
                    mailchimp_conn.lists.get_list_member(list_id, subscriber_hash)
                except Exception:
                    continue

                client_data = {}
                client_data["email_address"] = email
                client_data["merge_fields"] = {FIELDS_NO_MEMBERS["email"]: email}

                try:
                    mailchimp_conn.lists.update_list_member(list_id, subscriber_hash, client_data)
                except ApiClientError as e:
                    logger.warning(
                        "Error en update l'email {} en la llista {}:\n{}".format(
                            client_data["email_address"], mchimp_list["name"], e.text
                        )
                    )
                else:
                    mailchimp_conn.lists.create_list_member_note(
                        list_id,
                        new_subscriber_hash,
                        {
                            "note": "S'ha actualitzat l'e-mail {} per {} vía ERP".format(
                                old_email, email
                            )
                        },
                    )
                    logger.info(
                        "L'email {} s'ha actualitzat en la llista {}".format(
                            client_data["email_address"], mchimp_list["name"]
                        )
                    )

    @job(queue="mailchimp_tasks")
    def unsubscribe_client_email_in_all_lists_async(
        self, cursor, uid, ids, old_email, mailchimp_conn, context=None
    ):
        self.unsubscribe_client_email_in_all_lists(
            cursor, uid, ids, old_email, mailchimp_conn, context=None
        )

    def unsubscribe_client_email_in_all_lists(
        self, cursor, uid, ids, old_email, mailchimp_conn, context=None
    ):
        ''' Unsubscribe email of a client in all Mailchimp lists where it is subscribed '''
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        logging.getLogger(
            "openerp.{0}.unsubscribe_client_email_in_all_lists".format(__name__)
        )

        all_lists = mailchimp_conn.lists.get_all_lists(
            fields=["lists.id,lists.name"], count=100, email=old_email
        )["lists"]

        for mchimp_list in all_lists:
            list_id = mchimp_list["id"]
            self.archieve_mail_in_list_sync(cursor, uid, ids, list_id, mailchimp_conn)


ResPartnerAddress()
