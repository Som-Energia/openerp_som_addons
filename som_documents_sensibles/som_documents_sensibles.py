# -*- coding: utf-8 -*-

from osv import fields, osv
from tools.translate import _


class SomDocumentsSensiblesCategory(osv.osv):
    _name = "som.documents.sensibles.category"
    _description = "Sensible documents category"
    _columns = {
        "name": fields.char("Category Name", size=64, required=True, translate=True),
        "code": fields.char("Code", size=32, required=True),
    }
    _defaults = {
        "name": lambda *a: "none",
    }
    _order = "name"

    _sql_constraints = [
        ("name_unique", "unique (name)", _(u"Ja existeix la categoria de document sensible."))
    ]


SomDocumentsSensiblesCategory()


class SomDocumentsSensibles(osv.osv):
    """Model per documents sensibles d'un partner"""

    _name = "som.documents.sensibles"

    _columns = {
        "name": fields.char(_("Nom del document"), size=64, required=True),
        "data_recepcio": fields.date(_("Data recepcio"), required=True),
        "darrera_data_valida": fields.date(_("Darrera data vàlida"), required=True),
        "partner_id": fields.many2one("res.partner", "Client", size=64, required=True),
        "nif": fields.related("partner_id", "vat", type="char", string="NIF", readonly=True),
        "categoria": fields.many2one(
            "som.documents.sensibles.category", string="Categoria", required=True
        ),
        "create_uid": fields.many2one("res.users", "Creador", readonly=True, required=False),
    }
    _defaults = {
        "name": lambda *a: "document sensible",
    }


SomDocumentsSensibles()
