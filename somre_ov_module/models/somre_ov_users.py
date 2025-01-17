# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

from decorators import www_entry_point
from exceptions import NoSuchUser, NoDocumentVersions

from datetime import datetime


class SomreOvUsers(osv.osv):

    _name = "somre.ov.users"
    _inherits = {"res.partner": "partner_id"}

    @www_entry_point(
        expected_exceptions=NoSuchUser
    )
    def identify_login(self, cursor, uid, login):
        search_params = [
            ('vat', '=', login),
            ('active', '=', True),
            ('customer', '=', True)  # Get only providers
        ]
        ov_user_id = self.search(cursor, uid, search_params)
        if ov_user_id:
            ov_user = self.browse(cursor, uid, ov_user_id)[0]

            return dict(
                vat=ov_user.vat,
                name=ov_user.name,
                email=ov_user.address[0].email,
                roles=['staff'] if ov_user.is_staff else ['customer'],
                username=ov_user.vat,
            )
        raise NoSuchUser()

    def get_customer(self, cursor, uid, username):
        # Get user profile: for now recover customer profile
        search_params = [
            ('vat', '=', username),
            ('active', '=', True),
            ('customer', '=', True),
            ('reov_baixa', '=', False),
        ]
        ov_user_id = self.search(cursor, uid, search_params)
        if not ov_user_id:
            raise NoSuchUser()

        return self.browse(cursor, uid, ov_user_id)[0]

    @www_entry_point(
        expected_exceptions=NoSuchUser
    )
    def get_profile(self, cursor, uid, username):
        # Get user profile: for now recover customer profile
        partner = self.get_customer(cursor, uid, username)
        return dict(
            username=partner.vat,
            roles=['staff'] if partner.is_staff else ['customer'],
            vat=partner.vat,
            name=partner.name,
            email=partner.address[0].email,
            address=partner.address[0].street,
            city=partner.address[0].city if partner.address[0].city else None,
            zip=partner.address[0].zip,
            state=partner.address[0].state_id.name,
            phones=[
                partner.address[0][key]
                for key in ['phone', 'mobile']
                if partner.address[0][key]
            ],
            proxy_vat=partner.representante_id.vat if partner.representante_id else None,
            proxy_name=partner.representante_id.name if partner.representante_id else None,
            signed_documents=self._documents_signed_by_customer(cursor, uid, partner.vat),
        )

    @www_entry_point(
        expected_exceptions=(NoSuchUser, NoDocumentVersions)
    )
    def sign_document(self, cursor, uid, username, document):
        document_version_obj = self.pool.get('somre.ov.signed.document.type.version')
        signed_document_obj = self.pool.get('somre.ov.signed.document')

        signer = self.get_customer(cursor, uid, username)

        last_version_id = document_version_obj.search(cursor, uid, [
            ('type.code', '=', document)
        ], order='date desc', limit=1)
        if not last_version_id:
            raise NoDocumentVersions(document)

        signed_document_obj.create(cursor, uid, dict(
            signer=signer.id,
            document_version=last_version_id[0],
            signature_date=datetime.now().strftime('%Y-%m-%d'),
        ))
        last_version = document_version_obj.read(cursor, uid, last_version_id, ['date'])
        return dict(signed_version=last_version[0]['date'])

    def _documents_signed_by_customer(self, cursor, uid, username):
        signed_document_obj = self.pool.get('somre.ov.signed.document')

        signer = self.get_customer(cursor, uid, username)
        signature_ids = signed_document_obj.search(cursor, uid, [
            ('signer', '=', signer.id),
        ])
        return [
            dict(
                document=signature.document_version.type.code,
                version=signature.document_version.date,
            )
            for signature in signed_document_obj.browse(cursor, uid, signature_ids)
        ]

    def _check_vat_exist(self, cursor, user, ids):

        for ov_user in self.browse(cursor, user, ids):
            if ov_user.partner_id.vat:
                cursor.execute(
                    "SELECT rp.id "
                    "FROM somre_ov_users sou "
                    "INNER JOIN res_partner rp on rp.id=sou.partner_id "
                    "WHERE rp.vat = '" + ov_user.partner_id.vat + "' "
                    "AND sou.reov_baixa IS FALSE"
                )
                ov_user_with_vat = cursor.fetchall()
                if len(ov_user_with_vat) > 1:
                    return False
        return True

    def vat_change(self, cr, uid, ids, value, context={}):
        pids = self.read(cr, uid, ids, ['partner_id'])
        pids = [p['partner_id'][0] for p in pids]
        return self.pool.get("res.partner").vat_change(cr, uid, pids, value, context)

    _columns = {
        "partner_id": fields.many2one("res.partner", _("Client teste")),
        "is_staff": fields.boolean(_("És staff")),
        "reov_baixa": fields.boolean(_("Usuari de baixa")),
        "initial_password": fields.char(_("Initial password"), size=15),
    }

    _defaults = {
        "is_staff": lambda *a: False,
        "reov_baixa": lambda *a: False,
        "initial_password": lambda *a: '',
    }

    _constraints = [(_check_vat_exist, "You cannot have same VAT for two active members!", ["vat"])]

    _sql_constraints = [
        ("partner_id_uniq", "unique(partner_id)",
         "Ja existeix un usuari de la ov de representa per aquest client")
    ]


SomreOvUsers()
