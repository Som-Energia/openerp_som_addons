# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _


class WizardAfegirContracteBateriaVirtual(osv.osv_memory):
    """Wizard per afegir contractes a un bateria virtual"""

    _name = "wizard.afegir.contracte.bateria.virtual"
    _inherit = "wizard.afegir.contracte.bateria.virtual"

    def action_assignar_bateria_virtual(self, cursor, uid, ids, context=None):
        """
        Acció per assignar el contracte a la bateria virutal
        Es valida que una bateria virtual no pugui tenir més d'un origen
        """
        if context is None:
            context = {}

        bat_obj = self.pool.get("giscedata.bateria.virtual")
        origen_obj = self.pool.get("giscedata.bateria.virtual.origen")
        pol_obj = self.pool.get("giscedata.polissa")
        polissa_ids = context["active_ids"]

        self_fields = [
            "bateria_id",
            "es_receptor_descomptes",
            "es_origen_descomptes",
            "data_inici",
            "pes",
            "crear_bateria_automaticament",
        ]
        self_vals = self.read(cursor, uid, ids, self_fields, context=context)[0]

        # validacions
        if self_vals["bateria_id"] and self_vals["es_origen_descomptes"]:
            # Intentem afegir més d'una polissa com a origen a una bateria virtual
            if len(polissa_ids) > 1:
                raise osv.except_osv(
                    _("Error"),
                    _("Estas intentant afegir més d'una pólissa a la bateria virtual com a origen"),
                )

            origen_ids = bat_obj.read(cursor, uid, self_vals["bateria_id"], ["origen_ids"])[
                "origen_ids"
            ]
            # Intentem afegir una polissa com a origen a una bateria virtual que ja te origen
            origin_cups = []
            pol_cups = []
            if origen_ids:
                for origen_id in origen_ids:
                    orig_pol_id = int(
                        origen_obj.read(cursor, uid, origen_id, ["origen_ref"], context=context)[
                            "origen_ref"
                        ].split(",")[1]
                    )
                    pol_cups_id = pol_obj.read(cursor, uid, orig_pol_id, ["cups"], context=context)[
                        "cups"
                    ][0]
                    origin_cups.append(pol_cups_id)
                for pol_id in context.get("active_ids", []):
                    cups_pol_id = pol_obj.read(cursor, uid, pol_id, ["cups"], context=context)[
                        "cups"
                    ][0]
                    if cups_pol_id not in origin_cups:
                        raise osv.except_osv(
                            _("Error"),
                            _(
                                "La bateria virtual seleccionada ja té un origen amb un CUPS diferent."  # noqa: E501
                            ),
                        )
                    if pol_cups and (cups_pol_id not in pol_cups):
                        raise osv.except_osv(
                            _("Error"),
                            _(
                                "S'estan intentant assignar varies pòlisses amb diferent CUPS com a orígens de la bateria virtual."  # noqa: E501
                            ),
                        )
                    pol_cups.append(cups_pol_id)

        return super(WizardAfegirContracteBateriaVirtual, self).action_assignar_bateria_virtual(
            cursor, uid, ids, context=context
        )


WizardAfegirContracteBateriaVirtual()
