# -*- coding: utf-8 -*-
from datetime import datetime

from osv import osv


class GiscedataFacturacioValidationValidator(osv.osv):
    _inherit = 'giscedata.facturacio.validation.validator'
    _name = 'giscedata.facturacio.validation.validator'

    def check_factura_amb_expedient(self, cursor, uid, fact, parameters):
        for bat in fact.polissa_id.bateria_ids:
            if (datetime.strptime(bat.data_inici, '%Y-%m-%d') < datetime.today()
                    and (not bat.data_final or datetime.strptime(bat.data_final, '%Y-%m-%d') > datetime.today())):
                return super(GiscedataFacturacioValidationValidator, self).check_factura_amb_expedient(cursor, uid, fact, parameters)

        return None


GiscedataFacturacioValidationValidator()
