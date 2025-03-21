# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class SomreOvSignedDocumentType(osv.osv):

    _name = "somre.ov.signed.document.type"
    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'code': fields.char('Code', size=128, required=True),
    }

    _sql_constraints = [
        ('code_uniq', 'unique("code")', _('The name of the document type code must be unique!')),
    ]


SomreOvSignedDocumentType()


class SomreOvSignedDocumentTypeVersion(osv.osv):

    _name = "somre.ov.signed.document.type.version"

    def _get_name(self, cursor, uid, ids, field_name, arg, context=None):
        result = {}
        for rec in self.browse(cursor, uid, ids, context):
            result[rec.id] = "{code}_{version}".format(
                code=rec.type.code,
                version=rec.date,
            )
        return result

    _columns = {
        'name': fields.function(
            _get_name,
            method=True,
            string='Name',
            type="char",
            store=True,
            size=124
        ),
        'type': fields.many2one('somre.ov.signed.document.type', 'Type', required=True),
        'date': fields.datetime('Date'),
    }

    _sql_constraints = [
        ('type_date_uniq', 'unique("type","date")', _(
            'Only one version of the document is accepted by date!')),
    ]


SomreOvSignedDocumentTypeVersion()


class SomreOvSignedDocument(osv.osv):

    _name = "somre.ov.signed.document"

    def _get_name(self, cursor, uid, ids, field_name, arg, context=None):
        result = {}
        for rec in self.browse(cursor, uid, ids, context):
            result[rec.id] = "{version} signed by {signer}".format(
                version=rec.document_version.name,
                signer=rec.signer.name,
            )
        return result

    _columns = {
        'name': fields.function(
            _get_name,
            method=True,
            string='Name',
            type="char",
            store=True,
            size=124
        ),
        'signer': fields.many2one('somre.ov.users', 'Type', required=True),
        'document_version': fields.many2one(
            'somre.ov.signed.document.type.version',
            'Document version',
            required=True
        ),
        'signature_date': fields.datetime('Signature date'),  # Null means unsigned
    }

    _sql_constraints = [
        ('code_uniq', 'unique("code")', _('The name of the document type code must be unique!')),
    ]


SomreOvSignedDocument()
