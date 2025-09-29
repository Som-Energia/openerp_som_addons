# -*- coding: utf-8 -*-
from osv import osv


class GiscedataSwitchingB1_01(osv.osv):
    """Classe pel pas 01"""

    _name = "giscedata.switching.b1.01"
    _inherit = "giscedata.switching.b1.01"

    def config_step(self, cursor, uid, ids, vals, context=None):
        """
        Changes step vals accordingly with vals dict:
            'phone_pre' & 'phone_num': Contact phone info
        """
        pas = self.browse(cursor, uid, ids, context=context)
        new_vals = vals.copy()

        if not new_vals.get("phone_num", False):
            del new_vals["phone_pre"]
            del new_vals["phone_num"]
        else:
            tel_obj = self.pool.get("giscedata.switching.telefon")
            tel_id = tel_obj.create(
                cursor, uid, {"numero": new_vals["phone_num"], "prefix": new_vals["phone_pre"]}
            )
            new_vals.update(
                {
                    "cont_nom": pas.cont_nom,
                    "cont_telefons": [(6, 0, [tel_id])],
                }
            )
            if not pas.telefons or (pas.telefons and not pas.telefons[0].numero):
                new_vals.update(
                    {
                        "telefons": [(6, 0, [tel_id])],
                    }
                )
            del new_vals["phone_pre"]
            del new_vals["phone_num"]

        super(GiscedataSwitchingB1_01, self).config_step(
            cursor, uid, ids, new_vals, context=None
        )


GiscedataSwitchingB1_01()
