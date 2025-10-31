# -*- coding: utf-8 -*-

from osv import osv
from tools.translate import _

import logging
from hashlib import md5
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
from oorq.decorators import job
from tools import config
import ast

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
    "nom_pila": "MMERGE12",
}

FIELDS_SOCIS = {
    "Cognoms_Nom": "MMERGE5",
    "NumSoci": "MMERGE4",
    "E-mail": "EMAIL",
    "Categoria": "MMERGE2",
    "Ciutat": "MMERGE3",
    "Provincia": "MMERGE6",
    "CodiPostal": "MMERGE7",
    "Idioma": "MMERGE8",
    "DomesticEmpresa": "MMERGE9",  # "domestic", "empresa", blanc (no té contractes)
    "Telefon": "MMERGE10",  # (###)###-####
    "Comarca": "MMERGE11",
    "NIF": "MMERGE1",
    "comunitat_autonoma": "MMERGE13",
    "Enllac": "MMERGE12",
    "Generation": "MMERGE14",  # "si", "no"
    "No rebre condicions generals": "MMERGE15",
    "Assamblea Virtual": "MMERGE16",
    "Nom empresa": "MMERGE17",
    "Proj. Transicio Energet": "MMERGE18",
    "Compra Coletiva": "MMERGE19",
    "contracte": "MMERGE22",  # "contracte_actiu", "contracte_esborrany", "sense_contracte"
    "autoproduccio": "AUTO",  # "amb autorpoduccio altres", "amb autoproduccio comp.simp.", "sense autoproduccio" # noqa: E501
    "nom_pila": "N_PILA",
    # blanc (no té contractes), "empresa amb maximetre", "empresa sense maximetre", "no es empresa"
    "maximetre": "MMERGE18",
    "ccvv": "MMERGE19",  # "CCVV","No CCVV"
}


class ResPartnerAddress(osv.osv):
    """
    Class to manage Mailchimp lists subscriptions
    This is the only class that should connect to Mailchimp API
    """

    _name = "res.partner.address"
    _inherit = "res.partner.address"

    def _get_mailchimp_client(self):
        return MailchimpMarketing.Client(
            dict(
                api_key=config.options.get("mailchimp_apikey"),
                server=config.options.get("mailchimp_server_prefix"),
            )
        )

    def _get_nom_pila(self, cursor, uid, ids, soci, empresa, context=None):
        # Nom pila
        if empresa or soci['vat'][2] == 'H':
            return ''
        else:
            return soci['name'].split(',')[-1].strip()

    def _es_empresa(self, cursor, uid, polissa_data, context=None):
        cat_pol_obj = self.pool.get('giscedata.polissa.category')
        category_names = cat_pol_obj.read(cursor, uid, polissa_data['category_id'], ['name'])
        for category in category_names:
            if category['name'] == 'Entitat o Empresa':
                return True
        return False

    def _get_contract_data(self, cursor, uid, partner_id, context=None):  # noqa: C901
        pol_obj = self.pool.get("giscedata.polissa")
        tar_obj = self.pool.get('giscedata.polissa.tarifa')
        soc_obj = self.pool.get('somenergia.soci')
        soci_id = soc_obj.search(cursor, uid, [('partner_id', '=', partner_id)])[0]
        soci = soc_obj.read(cursor, uid, soci_id, ['name', 'vat'])

        soci_data = {}
        TARIFES_MAXIMETRE = ['3.0TD', '3.0TDVE', '6.1TD', '6.1TDVE', '6.2TD', '6.3TD', '6.4TD']

        polisses_ids = pol_obj.search(cursor, uid, [('titular', '=', partner_id)])
        contracte_actiu = False
        contracte_esborrany = False
        empresa = False
        for polissa_id in polisses_ids:
            polissa_data = pol_obj.read(cursor, uid, polissa_id, [
                                        'state', 'category_id', 'tarifa', 'potencia'])
            if polissa_data['state'] == 'activa':
                contracte_actiu = True
                empresa = empresa or self._es_empresa(cursor, uid, polissa_data, context)
                break
            if polissa_data['state'] == 'esborrany':
                contracte_esborrany = True
                empresa = empresa or self._es_empresa(cursor, uid, polissa_data, context)

        if contracte_actiu:
            soci_data['contracte'] = 'contracte_actiu'
        elif contracte_esborrany:
            soci_data['contracte'] = 'contracte_esborrany'
        if not polisses_ids:
            soci_data['contracte'] = 'sense_contracte'

        # Domèstic o empresa
        if empresa:
            soci_data['domestic_empresa'] = 'empresa'
        elif not empresa and polisses_ids:
            soci_data['domestic_empresa'] = 'domestic'
        else:
            soci_data['domestic_empresa'] = ''

        # Autoproduccio i Maxímetre
        amb_maximetre = False
        empresa = False
        auto = False
        compensacio = False
        for polissa_id in polisses_ids:
            polissa_data = pol_obj.read(
                cursor, uid, polissa_id, [
                    'state', 'category_id', 'tarifa', 'potencia', 'autoconsumo'])
            empresa = empresa or self._es_empresa(cursor, uid, polissa_data, context)
            tarifa_ids = tar_obj.search(cursor, uid, [('name', 'in', TARIFES_MAXIMETRE)])
            if (polissa_data['tarifa']
                and polissa_data['tarifa'][0] in tarifa_ids
                and polissa_data['potencia'] > 15
                    and polissa_data['potencia'] <= 50):
                amb_maximetre = True

            if polissa_data['autoconsumo'] in ['41', '42', '43']:
                auto = True
                compensacio = True
            elif polissa_data['autoconsumo'] != '00':
                auto = True

        if auto and compensacio:
            soci_data['autoproduccio'] = 'amb autoproducció comp.simp.'
        elif auto and not compensacio:
            soci_data['autoproduccio'] = 'amb autoproducció altres'
        else:
            soci_data['autoproduccio'] = 'sense autoproducció'

        if empresa:
            if amb_maximetre:
                soci_data['maximetre'] = 'empresa amb maxímetre'
            else:
                soci_data['maximetre'] = 'empresa sense maxímetre'
        elif polisses_ids:
            soci_data['maximetre'] = 'no és empresa'
        else:
            soci_data['maximetre'] = ''

        # CCVV
        if soci['vat'][2] == 'H':
            soci_data['ccvv'] = 'CCVV'
        else:
            soci_data['ccvv'] = 'No CCVV'

        soci_data['nom_pila'] = self._get_nom_pila(cursor, uid, partner_id, soci, empresa)

        return soci_data

    def _get_members_mailchimp_lists(self, cursor, uid, ids, context=None):
        conf_obj = self.pool.get("res.config")
        list_name_1 = conf_obj.get(cursor, uid, "mailchimp_socis_list", None)
        list_name_2 = conf_obj.get(cursor, uid, "mailchimp_socis_crinforma_list", None)
        members_list_names = [list_name_1, list_name_2]
        return members_list_names

    def write(self, cursor, uid, ids, vals, context=None):
        """ Override write to detect email changes and update Mailchimp """
        if context is None:
            context = {}

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        try:
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
        except Exception as e:
            sentry = self.pool.get('sentry.setup')
            if sentry:
                sentry.client.captureException()
            logger = logging.getLogger("openerp.{0}.res_partner_address.write".format(__name__))
            logger.warning("Error al comunicar amb Mailchimp {}".format(e.text))
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

    def fill_merge_fields_clients_from_partner(self, cursor, uid, partner_id, context=None):
        """Prepare the fields with the data of a member, to be sent to Mailchimp
        from res.partner id
        """
        try:
            partner_address_id = self.search(cursor, uid, [("partner_id", "=", partner_id)], limit=1)[0]  # noqa: E501
        except IndexError:
            raise osv.except_osv(_("Error"), _("Partner address not found. Partner ID: {}".format(partner_id)))  # noqa: E501
        return self.fill_merge_fields_clients(cursor, uid, partner_address_id, context=context)

    def fill_merge_fields_clients(self, cursor, uid, id, context=None):
        """
        Prepare the fields with the data of a non-member client, to be sent to Mailchimp
        """
        if isinstance(id, (list, tuple)):
            id = id[0]
        partner_obj = self.pool.get("res.partner")
        municipi_obj = self.pool.get("res.municipi")
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
                FIELDS_NO_MEMBERS["firstname"]: partner_fields["name"].split(",")[-1].strip(),
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

    def fill_merge_fields_soci_from_partner(self, cursor, uid, partner_id, context=None):
        """Prepare the fields with the data of a member, to be sent to Mailchimp
        from res.partner id
        """
        try:
            partner_address_id = self.search(cursor, uid, [("partner_id", "=", partner_id)], limit=1)[0]  # noqa: E501
        except IndexError:
            raise osv.except_osv(_("Error"), _("Partner address not found. Partner ID: {}".format(partner_id)))  # noqa: E501
        return self.fill_merge_fields_soci(cursor, uid, partner_address_id, context=context)

    def fill_merge_fields_soci(self, cursor, uid, id, context=None):
        """
        Prepare the fields with the data of a member, to be sent to Mailchimp
        from res.partner.address id
        """
        if isinstance(id, (list, tuple)):
            id = id[0]
        partner_obj = self.pool.get("res.partner")
        municipi_obj = self.pool.get("res.municipi")
        partner_data = self.read(
            cursor, uid, id, ["partner_id", "email", "zip", "id_municipi", "mobile", "phone"]
        )
        partner_fields = partner_obj.read(
            cursor, uid, partner_data["partner_id"][0], ["name", "lang", "vat", "ref"]
        )
        soci_data = self._get_contract_data(cursor, uid, partner_data["partner_id"][0], context)
        mailchimp_member = {
            "email_address": partner_data["email"],
            "status": "subscribed",
            "merge_fields": {
                FIELDS_SOCIS["Cognoms_Nom"]: partner_fields["name"],
                FIELDS_SOCIS["Idioma"]: partner_fields["lang"],
                FIELDS_SOCIS["E-mail"]: partner_data["email"],
                FIELDS_SOCIS["CodiPostal"]: partner_data["zip"],
                FIELDS_SOCIS["NIF"]: partner_fields["vat"],
                FIELDS_SOCIS["NumSoci"]: partner_fields["ref"],
                FIELDS_SOCIS["Telefon"]: partner_data["phone"]
                if partner_data["phone"]
                else partner_data["mobile"],
                # "domestic", "empresa", blanc (no té contractes)
                FIELDS_SOCIS["DomesticEmpresa"]: soci_data['domestic_empresa'],
                # "contracte_actiu", "contracte_esborrany", "sense_contracte"
                FIELDS_SOCIS["contracte"]: soci_data['contracte'],
                # "amb autorpoduccio altres", "amb autoproduccio comp.simp.", "sense autoproduccio"
                FIELDS_SOCIS["autoproduccio"]: soci_data['autoproduccio'],
                FIELDS_SOCIS["nom_pila"]: soci_data['nom_pila'],
                # blanc (no té contractes), "empresa amb maximetre", "empresa sense maximetre", "no es empresa" # noqa: E501
                FIELDS_SOCIS["maximetre"]: soci_data['maximetre'],
                FIELDS_SOCIS["ccvv"]: soci_data['ccvv'],  # "CCVV","No CCVV"
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

    def subscribe_partner_in_customers_no_members_lists(
            self, cursor, uid, partner_ids, context=None):
        if not isinstance(partner_ids, (list, tuple)):
            partner_ids = [partner_ids]

        MAILCHIMP_CLIENT = self._get_mailchimp_client()
        conf_obj = self.pool.get("res.config")
        list_name = conf_obj.get(cursor, uid, "mailchimp_clients_list", None)
        list_id = self.get_mailchimp_list_id(list_name, MAILCHIMP_CLIENT)

        for _id in partner_ids:
            client_data = self.fill_merge_fields_clients_from_partner(cursor, uid, _id)
            self.subscribe_mail_in_list_async(
                cursor, uid, [client_data], list_id, MAILCHIMP_CLIENT
            )

    def subscribe_partner_in_members_lists(self, cursor, uid, partner_ids, context=None):
        if not isinstance(partner_ids, (list, tuple)):
            partner_ids = [partner_ids]

        MAILCHIMP_CLIENT = self._get_mailchimp_client()
        list_names = self._get_members_mailchimp_lists(cursor, uid, partner_ids, context=context)
        list_ids = [self.get_mailchimp_list_id(name, MAILCHIMP_CLIENT) for name in list_names]

        for _id in partner_ids:
            client_data = self.fill_merge_fields_soci_from_partner(cursor, uid, _id)
            for list_id in list_ids:
                self.subscribe_mail_in_list_async(
                    cursor, uid, [client_data], list_id, MAILCHIMP_CLIENT
                )

    @job(queue="mailchimp_tasks")
    def subscribe_mail_in_list_async(
        self, cursor, uid, clients_data, list_id, mailchimp_conn, context=None
    ):
        return self.subscribe_mail_in_list(
            cursor, uid, clients_data, list_id, mailchimp_conn, context=context)

    def subscribe_mail_in_list(
        self, cursor, uid, clients_data, list_id, mailchimp_conn, context=None
    ):
        """ Subscribe a list of clients to a Mailchimp list """
        logger = logging.getLogger("openerp.{0}.subscribe_mail_in_list".format(__name__))
        for client_data in clients_data:
            try:
                mailchimp_conn.lists.add_list_member(list_id, client_data)
            except ApiClientError as e:
                if e.status_code == 400 and ast.literal_eval(e.text)['title'] == 'Member Exists':
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
            else:
                logger.info("Mailchimp: Email subscrit a la llista {}: {}".format(
                    list_id, client_data["email_address"]))

    @job(queue="mailchimp_tasks")
    def update_members_data_mailchimp_async(self, cursor, uid, partner_ids, context=None):
        self.update_members_data_mailchimp_sync(cursor, uid, partner_ids, context=context)

    def update_members_data_mailchimp_sync(self, cursor, uid, partner_ids, context=None):
        if not isinstance(partner_ids, (list, tuple)):
            partner_ids = [partner_ids]
        logger = logging.getLogger("openerp.{0}.update_members_data_mailchimp".format(__name__))
        MAILCHIMP_CLIENT = self._get_mailchimp_client()
        list_names = self._get_members_mailchimp_lists(cursor, uid, partner_ids, context=context)
        list_ids = [self.get_mailchimp_list_id(name, MAILCHIMP_CLIENT) for name in list_names]

        for _id in partner_ids:
            client_data = self.fill_merge_fields_soci_from_partner(cursor, uid, _id)
            try:
                subscriber_hash = md5(client_data["email_address"].lower()).hexdigest()
                for list_id in list_ids:
                    MAILCHIMP_CLIENT.lists.update_list_member(list_id, subscriber_hash, client_data)
            except ApiClientError as e:
                if e.status_code == 404:
                    logger.warning(
                        "L'API no ha permès actualitzar l'email {}. "
                        "Error comú quan el mail no es troba a la llista: "
                        "Error de l'API: {}".format(client_data["email_address"], e.text)
                    )
                    self.subscribe_partner_in_members_lists(cursor, uid, partner_ids, context)
                else:
                    raise osv.except_osv(
                        _("Error"),
                        _(
                            "Error en actualitzar l'email {}:\n{}".format(
                                client_data["email_address"], e.text
                            )
                        ),
                    )
            else:
                logger.info("Mailchimp: Email actualitzat a la llista {}: {}".format(
                    list_id, client_data["email_address"]))

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
                        "Mailchimp: L'email {} s'ha actualitzat en la llista {}".format(
                            client_data["email_address"], mchimp_list["name"]
                        )
                    )

    @job(queue="mailchimp_tasks")
    def update_or_create_data_in_list_mailchimp_async(self, cursor, uid, clients_data, list_names, context=None):  # noqa: E501
        self.update_or_create_data_in_list_mailchimp(
            cursor, uid, clients_data, list_names, context=context)

    def update_or_create_data_in_list_mailchimp(self, cursor, uid, clients_data, list_names, context=None):  # noqa: E501
        if not isinstance(clients_data, (list, tuple)):
            clients_data = [clients_data]
        if not isinstance(list_names, (list, tuple)):
            list_names = [list_names]
        logger = logging.getLogger("openerp.{0}.update_data_in_list_mailchimp".format(__name__))
        MAILCHIMP_CLIENT = self._get_mailchimp_client()
        list_ids = [self.get_mailchimp_list_id(name, MAILCHIMP_CLIENT) for name in list_names]
        for client_data in clients_data:
            try:
                if client_data.get("email_address", False):
                    subscriber_hash = md5(client_data["email_address"].lower()).hexdigest()
                    for list_id in list_ids:
                        MAILCHIMP_CLIENT.lists.set_list_member(
                            list_id, subscriber_hash, client_data)
            except ApiClientError as e:
                raise osv.except_osv(
                    _("Error"),
                    _(
                        "Error en actualitzar l'email {}:\n{}".format(
                            client_data["email_address"], e.text
                        )
                    ),
                )
            else:
                logger.info("Mailchimp: Email actualitzat a la llista {}: {}".format(
                    list_id, client_data["email_address"]))

    def unsubscribe_partner_in_customers_no_members_lists(
            self, cursor, uid, partner_ids, context=None):
        if not isinstance(partner_ids, (list, tuple)):
            partner_ids = [partner_ids]

        MAILCHIMP_CLIENT = self._get_mailchimp_client()
        conf_obj = self.pool.get("res.config")
        list_name = conf_obj.get(cursor, uid, "mailchimp_clients_list", None)
        list_id = self.get_mailchimp_list_id(list_name, MAILCHIMP_CLIENT)

        for _id in partner_ids:
            self.archieve_mail_in_list(
                cursor, uid, _id, list_id, MAILCHIMP_CLIENT
            )

    def unsubscribe_partner_in_members_lists(self, cursor, uid, partner_ids, context=None):
        if not isinstance(partner_ids, (list, tuple)):
            partner_ids = [partner_ids]

        MAILCHIMP_CLIENT = self._get_mailchimp_client()
        list_names = self._get_members_mailchimp_lists(cursor, uid, partner_ids, context=context)
        list_ids = [self.get_mailchimp_list_id(name, MAILCHIMP_CLIENT) for name in list_names]

        for _id in partner_ids:
            for list_id in list_ids:
                self.archieve_mail_in_list(
                    cursor, uid, _id, list_id, MAILCHIMP_CLIENT
                )

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
            if not email["email"]:
                logger.info("Mailchimp: No s'ha pogut arxivar perquè la fitxa del client"
                            "no te email. res.partner.address id = {}".format(email["id"]))
                continue
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
                logger.info("Mailchimp: Email arxivat a la llista {}: {}".format(list_id, email))

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
