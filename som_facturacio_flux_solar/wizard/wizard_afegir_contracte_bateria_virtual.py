# -*- coding: utf-8 -*-
from osv import osv


class WizardAfegirContracteBateriaVirtual(osv.osv_memory):
    """Wizard per afegir contractes a un bateria virtual"""

    _name = "wizard.afegir.contracte.bateria.virtual"
    _inherit = "wizard.afegir.contracte.bateria.virtual"

    def create_origen_with_given_data(
        self, cursor, uid, wiz_vals, polissa_id, bateria_id, context=None
    ):
        """Mètode extret per a poder sobreescriure / sobrecarregar en mòduls custom"""
        if context is None:
            context = {}

        bat_origen_obj = self.pool.get("giscedata.bateria.virtual.origen")
        origen_fields = {
            "data_ultim_dia_calculat": wiz_vals["data_inici"],
            "data_inici_descomptes": wiz_vals["data_inici"],
            "origen_ref": "giscedata.polissa,%s" % polissa_id,
            "bateria_id": bateria_id,
        }
        origen_id = bat_origen_obj.create(cursor, uid, origen_fields, context=context)
        return origen_id

    def get_auto_bat_name(self, cursor, uid, polissa_id, polissa_name, context=None):
        if context is None:
            context = {}
        return "FS" + str(polissa_name)


WizardAfegirContracteBateriaVirtual()
