# -*- coding: utf-8 -*-
from osv import osv
from tools import cache

class AccountInvoice(osv.osv):

    _name = 'account.invoice'
    _inherit = 'account.invoice'

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
        import pudb;pu.db
        exact = self.exact_search(cr, user, context=context)
        for idx, arg in enumerate(args):
            if len(arg) == 3:
                field, operator, match = arg
                if field == 'number' and isinstance(match,(unicode,str)):
                    if exact and not '%' in match:
                        operator = '='
                    args[idx] = (field, operator, match)
        return super(AccountInvoice, self).search(cr, user, args, offset, limit, order, context, count)

    def _auto_init(self, cr, context={}):
        result = super(AccountInvoice, self)._auto_init(cr, context)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'account_invoice_number_index\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX account_invoice_number_index ON account_invoice(number)')
        return result


AccountInvoice()