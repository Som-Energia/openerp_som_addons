# -*- coding: utf-8 -*-
from osv import osv


class GiscedataFacturacioValidationValidator(osv.osv):
    _inherit = 'giscedata.facturacio.validation.validator'
    _name = 'giscedata.facturacio.validation.validator'

    def check_factura_amb_expedient(self, cursor, uid, fact, parameters):
        if fact.polissa_id.bateria_ids:
            return super(GiscedataFacturacioValidationValidator).check_factura_amb_expedient(cursor, uid, fact, parameters)

        return None


GiscedataFacturacioValidationValidator()
