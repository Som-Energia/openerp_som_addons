# -*- coding: utf-8 -*-
from osv import osv

from decorators import www_entry_point
from exceptions import NoSuchUser, NoDocumentVersions

from datetime import datetime


class SomreOvUsers(osv.osv_memory):

    _name = "somre.ov.users"

    @www_entry_point(
        expected_exceptions=NoSuchUser
    )
    def identify_login(self, cursor, uid, login):
        partner_obj = self.pool.get('res.partner')
        search_params = [
            ('vat', '=', login),
            ('active', '=', True),
            ('customer', '=', True)  # Get only providers
        ]
        partner_id = partner_obj.search(cursor, uid, search_params)
        if partner_id:
            partner = partner_obj.browse(cursor, uid, partner_id)[0]

            return dict(
                vat=partner.vat,
                name=partner.name,
                email=partner.address[0].email,
                roles=['staff'] if self.partner_is_staff(cursor, uid, partner.id) else ['customer'],
                username=partner.vat,
            )
        raise NoSuchUser()

    def partner_is_staff(self, cursor, uid, partner_id):
        address_obj = self.pool.get('res.partner.address')
        search_params = [
            ('partner_id', '=', partner_id),
        ]
        partner_adddress_ids = address_obj.search(cursor, uid, search_params)
        if partner_adddress_ids:
            user_obj = self.pool.get('res.users')
            search_params = [
                ('address_id', '=', partner_adddress_ids[0]),
            ]
            user = user_obj.search(cursor, uid, search_params)
            if user:
                return True
        return False

    def get_customer(self, cursor, uid, username):
        # Get user profile: for now recover customer profile
        partner_obj = self.pool.get('res.partner')
        search_params = [
            ('vat', '=', username),
            ('active', '=', True),
            ('customer', '=', True),
        ]
        partner_id = partner_obj.search(cursor, uid, search_params)
        if not partner_id:
            raise NoSuchUser()

        return partner_obj.browse(cursor, uid, partner_id)[0]

    @www_entry_point(
        expected_exceptions=NoSuchUser
    )
    def get_profile(self, cursor, uid, username):
        # Get user profile: for now recover customer profile
        partner = self.get_customer(cursor, uid, username)
        return dict(
            username=partner.vat,
            roles=['staff'] if self.partner_is_staff(cursor, uid, partner.id) else ['customer'],
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


SomreOvUsers()
