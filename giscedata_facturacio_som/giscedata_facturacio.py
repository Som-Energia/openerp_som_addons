# -*- coding: utf-8 -*-
from osv import osv
from tools import cache

class GiscedataFacturacio(osv.osv):
    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'


    @cache(timeout=5 * 60)
    def exact_search(self, cursor, uid, context=None):
        if context is None:
            context = {}
        exact = int(self.pool.get('res.config').get(
            cursor, uid, 'account_invoice_number_cerca_exacte', '0')
        )
        return exact

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        """Funció per fer cerques per number exacte, enlloc d'amb 'ilike'.
        """
        exact = self.exact_search(cr, user, context=context)
        if exact:
            for idx, arg in enumerate(args):
                if len(arg) == 3:
                    field, operator, match = arg
                    if field == 'number' and isinstance(match,(unicode,str)):
                        if not '%' in match:
                            operator = '='
                        args[idx] = (field, operator, match)
        return super(GiscedataFacturacio, self).search(cr, user, args, offset, limit, order, context, count)


GiscedataFacturacio()