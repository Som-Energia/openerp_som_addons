# -*- coding: utf-8 -*-
"""Modificacions del model giscedata_facturacio_factura per SOMENERGIA.
"""

from osv import osv, fields
from tools.misc import cache


class GiscedataFacturacioFactura(osv.osv):
    """Classe per la factura de comercialitzadora."""
    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    @cache(timeout=10)
    def _fnc_per_enviar(self, cursor, uid, ids, field_name, args,
                        context=None):
        """Retorna si una factura està marcada per enviar o no.
        """
        res = dict([(x, 'email') for x in ids])

        cursor.execute("""
            select
              f.id,
              p.enviament
            from
              giscedata_facturacio_factura f
              left join giscedata_polissa p
                on (p.id = f.polissa_id)
              left join account_invoice i on (f.invoice_id = i.id)
            where
              f.id in %s
              and p.state = 'baixa'
        """, (tuple(ids), ))
        res.update(dict([(x[0], x[1]) for x in cursor.fetchall()]))

        cursor.execute("""
            select
              f.id,
              m.enviament
            from
              giscedata_facturacio_factura f
              left join giscedata_polissa_modcontractual m
                on (m.polissa_id = f.polissa_id)
            where
              f.id in %s
              and f.data_final between m.data_inici and m.data_final
        """, (tuple(ids), ))
        res.update(dict([(x[0], x[1]) for x in cursor.fetchall()]))

        cursor.execute("""
            select
              f.id,
              m.enviament
            from
              giscedata_facturacio_factura f
              left join giscedata_polissa_modcontractual m
                on (m.polissa_id = f.polissa_id)
              left join account_invoice i on (f.invoice_id = i.id)
            where
              f.id in %s
              and i.date_invoice between m.data_inici and m.data_final
        """, (tuple(ids), ))
        res.update(dict([(x[0], x[1]) for x in cursor.fetchall()]))
        return res


    _columns = {
        'per_enviar': fields.function(
            _fnc_per_enviar,
            method=True,
            type='selection',
            selection=[('email', 'E-mail'), ('postal', 'Correu postal')],
            string='Tipus d\'enviament',
            store=True,
            select=2
        ),
    }


GiscedataFacturacioFactura()