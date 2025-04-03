# -*- coding: utf-8 -*-
"""
Nou modesl de dades per gestionar els percentatges d'acumulacio dels origens de bateria virtual per SOMENERGIA.  # noqa: E501
"""

from osv import osv, fields
from tools.translate import _
from osv.orm import PgView
from addons import get_module_resource


class GiscedataBateriaVirtualPercentatgesAcumulacio(osv.osv):

    _name = "giscedata.bateria.virtual.percentatges.acumulacio"
    _description = _("Bateria virtual percentatge acumulable")

    _columns = {
        "percentatge": fields.integer(
            "Pecentatge", help=_("Percentatge que acumula la bateria virtual")
        ),
        "data_inici": fields.date(_("Data inici"), required=True),
        "data_fi": fields.date(_("Data fi")),
        "origen_id": fields.many2one(
            "giscedata.bateria.virtual.origen", "Origen", ondelete="cascade"
        ),
    }

    _defaults = {
        "percentatge": lambda *a: 100,
    }


GiscedataBateriaVirtualPercentatgesAcumulacio()


class GiscedataPolissa(osv.osv):

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def wkf_baixa(self, cursor, uid, ids):
        # Afegir la data de baixa al percentatge d'acumulacio de la bateria virtual quan es dona de baixa la polissa  # noqa: E501

        res = super(GiscedataPolissa, self).wkf_baixa(cursor, uid, ids)

        pol_obj = self.pool.get("giscedata.polissa")
        bat_percentatge_obj = self.pool.get("giscedata.bateria.virtual.percentatges.acumulacio")

        for pol_id in ids:
            pol_br = pol_obj.browse(cursor, uid, pol_id, context={"prefetch": False})
            for pol_bat_br in pol_br.bateria_ids:
                for orig_br in pol_bat_br.bateria_id.origen_ids:
                    for percentatge_acum_br in orig_br.percentatges_acumulacio:
                        if (
                            not percentatge_acum_br.data_fi
                            or percentatge_acum_br.data_fi > pol_br.data_baixa
                        ):
                            bat_percentatge_obj.write(
                                cursor, uid, percentatge_acum_br.id, {"data_fi": pol_br.data_baixa}
                            )
        return res


GiscedataPolissa()

class GiscedataBateriaVirtualResumFacturacio(PgView, osv.osv):

    _inherit = 'giscedata.bateria.virtual.resum.facturacio'
    _view_file = get_module_resource('giscedata_facturacio_bateria_virtual', 'sql', 'detall_bateria_virtual_resum_facturacio_percentatges_acumulacio.sql')


GiscedataBateriaVirtualResumFacturacio()