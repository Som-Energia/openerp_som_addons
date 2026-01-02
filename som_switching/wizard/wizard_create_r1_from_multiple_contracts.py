# -*- coding: utf-8 -*-

from osv import fields, osv
from gestionatr.defs import TABLA_87


class WizardR101FromMultipleContracts(osv.osv_memory):
    _name = "wizard.r101.from.multiple.contracts"
    _inherit = "wizard.r101.from.multiple.contracts"

    def create_r1_from_contracts(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        ctx = context.copy()
        info = self.read(cursor, uid, ids, [
            "facturacio_suspesa", "refacturacio_pendent", "reclamacio_disconformidad_autoconsumo",
            "reclamacio_tipus_concepte_facturat", "reclamacio_tipus_atencio_incorrecte"
        ], context=context)[0]
        info.pop("id")
        ctx.update({"extra_r1_vals": info})

        res = super(WizardR101FromMultipleContracts, self).create_r1_from_contracts(
            cursor, uid, ids, context=ctx
        )

        return res

    def onchange_subtipus(self, cursor, uid, ids, subtipus, context=None):
        if context is None:
            context = {}
        res = super(WizardR101FromMultipleContracts, self).onchange_subtipus(
            cursor, uid, ids, subtipus, context=context
        )
        if subtipus:
            subtipus_obj = self.pool.get("giscedata.subtipus.reclamacio")
            subinfo = subtipus_obj.read(cursor, uid, subtipus, ["name"], context=context)
            if subinfo["name"] in ("036", "009"):
                res["value"].update({"facturacio_suspesa": True, "refacturacio_pendent": True})
            if subinfo["name"] != "001":
                res["value"].update({
                    "reclamacio_tipus_atencio_incorrecte": False
                })
            if subinfo["name"] != "008":
                res["value"].update({
                    "reclamacio_tipus_concepte_facturat": False
                })
            if subinfo["name"] != "075":
                res["value"].update({
                    "reclamacio_disconformidad_autoconsumo": False
                })
            res["value"].update({'subtipus_code': subinfo['name']})
        return res

    _columns = {
        "facturacio_suspesa": fields.boolean("Marcar contracte amb facturació suspesa"),
        "refacturacio_pendent": fields.boolean("Marcar contracte amb refacturacio pendent"),
        "subtipus_code": fields.char('Codi subtipus', size=4),
        'reclamacio_disconformidad_autoconsumo': fields.many2many(
            'giscedata.disconformidad.autoconsumo', 'rel_disconformitat_wiz_create_r1',
            'wiz_id', 'disconformitat_id', 'Disconformitat autoconsum'
        ),
        'reclamacio_tipus_concepte_facturat': fields.many2many(
            'giscedata.tipo.concepto.facturado', 'rel_concepte_facturat_wiz_create_r1',
            'wiz_id', 'tipus_concepte_facturat_id', 'Tipus concepte facturat'
        ),
        'reclamacio_tipus_atencio_incorrecte': fields.selection(
            [t[:2] for t in TABLA_87], u'Tipus atenció incorrecte',
        ),
    }

    _defaults = {
        "subtipus_code": lambda *a: '000',
    }


WizardR101FromMultipleContracts()
