# -*- coding: utf-8 -*-
from osv import osv
from tools import cache
from datetime import datetime


class GiscedataFacturacio(osv.osv):
    _name = "giscedata.facturacio.factura"
    _inherit = "giscedata.facturacio.factura"

    @cache(timeout=5 * 60)
    def exact_number_search(self, cursor, uid, context=None):
        if context is None:
            context = {}
        exact = int(
            self.pool.get("res.config").get(cursor, uid, "account_invoice_number_cerca_exacte", "0")
        )
        return exact

    @cache(timeout=5 * 60)
    def exact_origin_search(self, cursor, uid, context=None):
        if context is None:
            context = {}
        exact = int(
            self.pool.get("res.config").get(cursor, uid, "invoice_origin_cerca_exacte", "0")
        )
        return exact

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        """Funció per fer cerques per number exacte, enlloc d'amb 'ilike'."""
        exact_number = self.exact_number_search(cr, user, context=context)
        exact_origin = self.exact_origin_search(cr, user, context=context)
        if exact_number or exact_origin:
            for idx, arg in enumerate(args):
                if len(arg) == 3:
                    field, operator, match = arg
                    if exact_number and field == "number" and isinstance(match, (unicode, str)):  # noqa: E501, F821
                        if "%" not in match:
                            operator = "="
                        args[idx] = (field, operator, match)
                    if exact_origin and field == "origin" and isinstance(match, (unicode, str)):  # noqa: E501, F821
                        if "%" not in match:
                            operator = "="
                        args[idx] = (field, operator, match)
        return super(GiscedataFacturacio, self).search(
            cr, user, args, offset, limit, order, context, count
        )


GiscedataFacturacio()

class GiscedataFacturacioFactura(osv.osv):
    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    def invoice_open(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        for fact_id in ids:
            polissa_id = self.read(cursor, uid, fact_id, ['polissa_id'])['polissa_id'][0]
            polissa_obj = self.pool.get('giscedata.polissa')
            pol_data = polissa_obj.read(cursor, uid, polissa_id, ['cobrament_bloquejat', 'estat_pendent_cobrament'])
            if pol_data['cobrament_bloquejat']:
                ptype_obj = self.pool.get('payment.type')
                ptype_id = ptype_obj.search(cursor, uid, [('name', '=', 'No remesables')])[0]
                now = datetime.today().strftime('%Y-%m-%d')
                observations = now + "EQUIP FACTURA - Pólissa en estat Facturació amb cobrament bloquejat"
                write_vals = {'payment_type': ptype_id,
                              'pending_state': pol_data['estat_pendent_cobrament'],
                              'comment': observations}
                self.write(cursor, uid, fact_id, write_vals)

        res = super(GiscedataFacturacioFactura,
                    self).invoice_open(cursor, uid, ids, context)

        for fact_id in ids:
            polissa_id = self.read(cursor, uid, fact_id, ['polissa_id'])['polissa_id'][0]
            polissa_obj = self.pool.get('giscedata.polissa')
            pol_data = polissa_obj.read(cursor, uid, polissa_id, ['cobrament_bloquejat', 'estat_pendent_cobrament'])
            if pol_data['cobrament_bloquejat']:
                ptype_obj = self.pool.get('payment.type')
                ptype_id = ptype_obj.search(cursor, uid, [('name', '=', 'No remesables')])[0]
                now = datetime.today().strftime('%Y-%m-%d')
                observations = now + "EQUIP FACTURA - Pólissa en estat Facturació amb cobrament bloquejat"
                write_vals = {'payment_type': ptype_id,
                              'comment': observations}
                self.write(cursor, uid, fact_id, write_vals)
                self.set_pending(cursor, uid, [fact_id], pol_data['estat_pendent_cobrament'][0])

        return res


GiscedataFacturacioFactura()
