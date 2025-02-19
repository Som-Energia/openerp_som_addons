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
        "data_alta_autoconsum": fields.date(
            "Data alta autoconsum (M105)",
            help="Data en la que es va activar la modcon "
            "de canvi de tipus d'auto de 00 al tipus"
            "oportú.",
        ),
        "data_baixa_autoconsum": fields.date(
            "Data baixa autoconsum (M105)",
            help="Data en la que es va activar la "
            "modcon de sortida de l'autoconsum "
            "del tipus que tingués a 00",
        ),
    }
    _defaults = {
        "data_alta_autoconsum": lambda *a: False,
        "data_baixa_autoconsum": lambda *a: False,
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

        fields_to_read = ["tipus_autoconsum", "data_inici", "modcontractual_ant", "polissa_id"]

        modcon_info = self.read(cursor, uid, mod_id, fields_to_read)
        auto_vals = {}
        if modcon_info.get("modcontractual_ant"):
            modcon_ant_info = self.read(
                cursor, uid, modcon_info["modcontractual_ant"][0], fields_to_read
            )
            if (
                modcon_ant_info.get("tipus_autoconsum") != modcon_info["tipus_autoconsum"]
                and modcon_ant_info["tipus_autoconsum"] == "00"
            ):
                auto_vals.update({"data_alta_autoconsum": modcon_info["data_inici"]})
            elif (
                modcon_ant_info.get("tipus_autoconsum") != modcon_info["tipus_autoconsum"]
                and modcon_info["tipus_autoconsum"] == "00"
            ):
                auto_vals.update({"data_baixa_autoconsum": modcon_info["data_inici"]})
        else:
            if modcon_info["tipus_autoconsum"] != "00":
                auto_vals.update({"data_alta_autoconsum": modcon_info["data_inici"]})

        if auto_vals:
            polissa_obj = self.pool.get("giscedata.polissa")
            polissa_obj.write(
                cursor,
                uid,
                [modcon_info["polissa_id"][0]],
                auto_vals,
                context={"skip_cnt_llista_preu_compatible": True},
            )


GiscedataPolissaModcontractual()
