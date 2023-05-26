# -*- coding: utf-8 -*-
import time
from osv import fields, osv
from tools.translate import _
from datetime import datetime

STATES_GESTIO_DESCOMPTES = [
    ('no_aplicar', 'No aplicar descomptes'),
    ('aplicar', 'Aplicar descomptes disponibles')
]

class WizardAfegirContracteBateriaVirtual(osv.osv_memory):
    """Wizard per afegir contractes a un bateria virtual
    """
    _name = "wizard.afegir.contracte.bateria.virtual"
    _inherit = 'wizard.afegir.contracte.bateria.virtual'

    def action_assignar_bateria_virtual(self, cursor, uid, ids, context=None):
        """
        Acció per assignar el contracte a la bateria virutal
        Es valida que una bateria virtual no pugui tenir més d'un origen
        """
        if context is None:
            context = {}

        bat_obj = self.pool.get('giscedata.bateria.virtual')
        polissa_ids = context['active_ids']

        self_fields = [
            'bateria_id', 'es_receptor_descomptes',
            'es_origen_descomptes', 'data_inici', 'pes',
            'gestio_descomptes', 'crear_bateria_automaticament'
        ]
        self_vals = self.read(
            cursor, uid, ids, self_fields, context=context
        )[0]

        # validacions
        if self_vals['bateria_id'] and self_vals['es_origen_descomptes']:
            # Intentem afegir més d'una polissa com a origen a una bateria virtual
            if len(polissa_ids) > 1:
                raise osv.except_osv(
                    _("Error"),
                    _("Estas intentant afegir més d'una pólissa a la bateria virtual com a origen")
                )

            origen_ids = bat_obj.read(cursor, uid, self_vals['bateria_id'],
                                                 ['origen_ids'])['origen_ids']
            # Intentem afegir una polissa com a origen a una bateria virtual que ja te origen
            if origen_ids:
                raise osv.except_osv(
                    _("Error"),
                    _("La bateria virtual seleccionada ja te origen.")
                )

        return super(WizardAfegirContracteBateriaVirtual, self).action_assignar_bateria_virtual(
            cursor, uid, ids, context=context
        )

    _columns = {
        'gestio_descomptes': fields.selection(
            STATES_GESTIO_DESCOMPTES, 'Gestió dels descomptes'
        ),
    }


WizardAfegirContracteBateriaVirtual()
