# -*- coding: utf-8 -*-

from __future__ import absolute_import

from oorq.decorators import job
from osv import osv, fields
from osv.expression import OOQuery
from osv.orm import browse_record
import logging
import pooler
from tools import config


class SomenergiaSoci(osv.osv):
    """Class to manage GkWh info in User interface"""

    _name = "somenergia.soci"
    _inherits = {"res.partner": "partner_id"}

    # To inherit bas class functions "automatically"
    def call_parent(self, method, field, *args, **kwargs):
        args = list(args)
        if len(args) >= 3:
            ids = args[2]
            if all([str(x).isdigit() for x in ids]):
                base_ids = [x[field][0] for x in self.read(args[0], args[1], ids, [field])]
                args[2] = base_ids
            elif all([isinstance(x, browse_record) for x in ids]):
                args[2] = [getattr(x, field) for x in ids]
        args = tuple(args)
        return method(*args, **kwargs)

    # To inherit bas class functions "automatically"
    def __getattr__(self, item):
        for base, base_field in self._inherits.items():
            obj = self.pool.get(base)
            base = getattr(obj, item)
            if callable(base):
                return lambda *args, **kwargs: self.call_parent(base, base_field, *args, **kwargs)
            else:
                return base

    def create_one_soci(self, cursor, uid, partner_id, context=None):
        """Creates only one soci (member) from a partner"""
        if isinstance(partner_id, (tuple, list)):
            partner_id[0]

        vals = {"partner_id": partner_id}
        soci_id = self.search(cursor, uid, [("partner_id", "=", partner_id)], context=context)
        if soci_id:
            self.write(cursor, uid, soci_id[0], {"baixa": False, "data_baixa_soci": None})
        else:
            soci_id = self.create(cursor, uid, vals, context=context)

        return soci_id

    def create_socis(self, cr_orig, uid, ids, context=None):
        """creates a soci from a partner"""
        partner_obj = self.pool.get("res.partner")
        logger = logging.getLogger("openerp.{0}.create_soci".format(__name__))

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        partner_fields = ["name", "ref"]
        soci_ids = []
        for partner_id in ids:
            try:
                cursor = pooler.get_db_only(cr_orig.dbname).cursor()
                partner_vals = partner_obj.read(cursor, uid, partner_id, partner_fields)

                soci_id = self.create_one_soci(cursor, uid, partner_id, context=context)
                soci_ids.append(soci_id)

                logger.info(
                    u"Created soci {0} ({1}) from partner {2} ({3})".format(
                        soci_id, partner_vals["ref"], partner_vals["name"], partner_id
                    )
                )
                self.subscriu_socia_mailchimp_async(cursor, uid, soci_id, context=context)
                cursor.commit()
            except Exception as e:
                logger.error(
                    u"Error converting partner {0} ({1}:{2}) {3}".format(
                        partner_id, partner_vals["ref"], partner_vals["name"], e
                    )
                )
                cursor.rollback()
            finally:
                if cursor:
                    cursor.close()

        return soci_ids

    @job(queue="mailchimp_tasks")
    def subscriu_socia_mailchimp_async(self, cursor, uid, ids, context=None):
        """
        Archive member async method
        """
        return self.subscriu_socia_mailchimp(cursor, uid, ids, context=context)

    def subscriu_socia_mailchimp(self, cursor, uid, ids, context=None):
        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        res_partner_obj = self.pool.get("res.partner")
        soci_obj = self.pool.get("somenergia.soci")
        is_member = soci_obj.search(cursor, uid, [("partner_id", "=", ids), ("baixa", "=", False)])
        if is_member:
            return

        import mailchimp_marketing as MailchimpMarketing

        MAILCHIMP_CLIENT = MailchimpMarketing.Client(
            dict(
                api_key=config.options.get("mailchimp_apikey"),
                server=config.options.get("mailchimp_server_prefix"),
            )
        )

        res_partner_address_obj = self.pool.get("res.partner.address")
        conf_obj = self.pool.get("res.config")

        list_name = conf_obj.get(cursor, uid, "mailchimp_socis_list", None)

        list_id = res_partner_address_obj.get_mailchimp_list_id(list_name, MAILCHIMP_CLIENT)

        address_list = res_partner_obj.read(cursor, uid, ids, ["address"])["address"]
        res_partner_address_obj.subscribe_mail_in_list(
            cursor, uid, address_list, list_id, MAILCHIMP_CLIENT
        )

    def count_active_socis(self, cursor, uid):
        q = OOQuery(self, cursor, uid)
        sql = q.select(['id']).where([
            ('partner_id.active', '=', True),
            ('baixa', '=', False),
            ('partner_id.category_id.name', 'ilike', 'Soci'),
        ])
        cursor.execute(*sql)
        return cursor.rowcount

    def _ff_emails(self, cursor, uid, ids, field_name, args, context=None):
        """
        Search partners by email
        """
        partner_obj = self.pool.get("res.partner")
        return partner_obj._ff_emails(cursor, uid, ids, field_name, args, context=context)

    def _ff_emails_search(self, cursor, uid, obj, name, args, context=None):
        """
        Search partners by email
        """
        partner_obj = self.pool.get("res.partner")
        res = partner_obj._ff_emails_search(cursor, uid, obj, name, args, context=context)
        # Es retornen id's de partner. El soci es relaciona amb el partner amb
        # partner_id
        return [("partner_id", "in", res[0][2])]

    def _check_vat_exist(self, cursor, user, ids):

        for soci in self.browse(cursor, user, ids):
            if soci.partner_id.vat:
                cursor.execute(
                    "SELECT rp.id "
                    "FROM somenergia_soci ss "
                    "INNER JOIN res_partner rp on rp.id=ss.partner_id "
                    "WHERE rp.vat = '" + soci.partner_id.vat + "' "
                    "AND ss.data_baixa_soci IS NULL AND ss.baixa IS FALSE"
                )
                soci_with_vat = cursor.fetchall()
                if len(soci_with_vat) > 1:
                    return False
        return True

    _columns = {
        "partner_id": fields.many2one("res.partner", "Soci", required=True),
        "baixa": fields.boolean("Soci de baixa"),
        "data_baixa_soci": fields.date("Data de baixa"),
        "emails": fields.function(
            _ff_emails, type="text", string="Emails", fnct_search=_ff_emails_search, method=True
        ),
    }

    _defaults = {
        "baixa": lambda *a: False,
    }

    _constraints = [(_check_vat_exist, "You cannot have same VAT for two active members!", ["vat"])]

    _sql_constraints = [
        ("partner_id_uniq", "unique(partner_id)", "Ja existeix un soci per aquest client")
    ]


SomenergiaSoci()
