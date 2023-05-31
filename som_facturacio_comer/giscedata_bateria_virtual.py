# -*- coding: utf-8 -*-
"""Modificacions del model giscedata_facturacio_factura per SOMENERGIA.
"""
from datetime import datetime

from osv import osv, fields
from tools.translate import _

STATES_GESTIO_ACUMULACIO = [
    ('estandard', _("Acumular segons saldo d'excedents")),
    ('percentatge', _("Acumular saldo d'excedents (percentatge)")),
]

class GiscedataBateriaVirtualOrigen(osv.osv):
    _name = "giscedata.bateria.virtual.origen"
    _inherit = 'giscedata.bateria.virtual.origen'

    def get_bateria_virtual_origen_descomptes(self, cursor, uid, ids, data_final, context=None):
        # [descompte_date, price, 'giscedata.facturacio.factura, factura.id']
        # [05-05-2023, 25.3, 'giscedata.facturacio.factura, 3642']
        descomptes_totals = super(GiscedataBateriaVirtualOrigen, self).get_bateria_virtual_origen_descomptes(cursor, uid, ids, data_final, context=context)

        descomptes = []
        for id in ids:
            gestio_acumulacio = self.read(cursor, uid, id, ['gestio_acumulacio'], context=context)['gestio_acumulacio']
            if gestio_acumulacio == 'estandard':
                return descomptes_totals
            # per percentatge
            else:
                # aplicar el percentatge corresponent segons data, sobre el descompte total
                for descompte_total in descomptes_totals:
                    descompte_percentatge = self.get_descompte_amb_percentatge_acumulacio(cursor, uid, id, descompte_total)
                    descomptes.append(descompte_percentatge)
                return descomptes

    def get_descompte_amb_percentatge_acumulacio(self, cursor, uid, id, descompte_total):
        # [descompte_date, price, 'giscedata.facturacio.factura, factura.id']
        # [05-05-2023, 25.3, 'giscedata.facturacio.factura, 3642']
        percentatge_acum_obj = self.pool.get('giscedata.bateria.virtual.percentatges.acumulacio')

        descompte_data = descompte_total[0]
        descompte_preu = descompte_total[1]

        # todo: crec que es fa en una pr que no esta a testing
        descompte_ref = descompte_total[2]

        percetatge_acum_id = self.get_percentatge_acumulacio_from_date(cursor, uid, id, descompte_data)
        percentatge = percentatge_acum_obj.read(cursor, uid, percetatge_acum_id[0], ['percentatge'])['percentatge']
        amount = descompte_preu * (percentatge/100)
        return (descompte_data, amount, descompte_ref)

    def get_percentatge_acumulacio_from_date(self, cursor, uid, id, descompte_date):
        percentatge_acum_obj = self.pool.get('giscedata.bateria.virtual.percentatges.acumulacio')
        percetatge_acum_id = percentatge_acum_obj.search(cursor, uid, [
            ('origen_id', '=', id),
            ('data_inici', '<=', descompte_date),
            ('data_fi', '>=', descompte_date),
        ])
        if len(percetatge_acum_id) > 1:
            raise osv.except_osv(u"Error", _("Hi ha poercentatges d'acumulacio que comprenen dates en comú"))
        return percetatge_acum_id


    _columns = {
        'gestio_acumulacio': fields.selection(STATES_GESTIO_ACUMULACIO, "Gestió de l'acumulació"),
        'percentatges_acumulacio': fields.one2many('giscedata.bateria.virtual.percentatges.acumulacio', 'origen_id', 'Percentatges acumulacio'),
    }

    _defaults = {
        'gestio_acumulacio': lambda *a: 'estandard',
    }


GiscedataBateriaVirtualOrigen()