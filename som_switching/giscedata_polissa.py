# -*- coding: utf-8 -*-

from osv import osv, fields


class GiscedataPolissa(osv.osv):

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def write(self, cursor, user, ids, vals, context=None):
        if "facturacio_suspesa" in vals and not vals["facturacio_suspesa"]:
            vals.update({"observacio_suspesa": False})

        return super(GiscedataPolissa, self).write(cursor, user, ids, vals, context)

    _columns = {
        "data_alta_autoconsum": fields.date("Data alta autoconsum"),
    }
    _defaults = {
        "data_alta_autoconsum": lambda *a: False,
    }


GiscedataPolissa()


class GiscedataPolissaModcontractual(osv.osv):
    """Modificació Contractual d'una Pòlissa."""

    _name = "giscedata.polissa.modcontractual"
    _inherit = "giscedata.polissa.modcontractual"

    def aplicar_modificacio(self, cursor, uid, mod_id, polissa_id=None):

        super(GiscedataPolissaModcontractual, self).aplicar_modificacio(
            cursor, uid, mod_id, polissa_id
        )

        fields_to_read = ["autoconsumo", "autoconsum_id", "data_inici"]

        modcon_info = self.read(cursor, uid, mod_id, fields_to_read)

        if modcon_info["autoconsumo"] != "00" or modcon_info["autoconsum_id"]:
            polissa_obj = self.pool.get("giscedata.polissa")
            if not polissa_id:
                polissa_id = self.browse(cursor, uid, mod_id).polissa_id.id

            pol_data_alta_autoconsum = polissa_obj.read(
                cursor, uid, polissa_id, ["data_alta_autoconsum"]
            )["data_alta_autoconsum"]
            if not pol_data_alta_autoconsum:
                polissa_obj.write(
                    cursor,
                    uid,
                    [polissa_id],
                    {"data_alta_autoconsum": modcon_info["data_inici"]},
                    context={"skip_cnt_llista_preu_compatible": True},
                )


GiscedataPolissaModcontractual()
