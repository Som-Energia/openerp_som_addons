# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataFacturacioFactura(osv.osv):
    """Classe per la factura de comercialitzadora."""
    _name = 'giscedata.facturacio.factura'
    _inherit = 'giscedata.facturacio.factura'

    # Poweremails hooks
    def poweremail_create_callback(self, cursor, uid, ids, vals, context=None):
        if hasattr(super(GiscedataFacturacioFactura, self), 'poweremail_create_callback'):
            super(GiscedataFacturacioFactura, self).poweremail_create_callback(
                cursor, uid, ids, vals, context=context
            )

        if vals['id']:
            self.write(cursor, uid, ids, {'enviat_mail_id': vals['id']})
        return True

    def poweremail_unlink_callback(self, cursor, uid, ids, context=None):
        if hasattr(super(GiscedataFacturacioFactura, self), 'poweremail_unlink_callback'):
            super(GiscedataFacturacioFactura, self).poweremail_unlink_callback(
                cursor, uid, ids, context=context
            )
        self.write(cursor, uid, ids, {'enviat_mail_id': None})
        return True

    def poweremail_write_callback(self, cursor, uid, ids, vals, context=None):
        if hasattr(super(GiscedataFacturacioFactura, self), 'poweremail_write_callback'):
            super(GiscedataFacturacioFactura, self).poweremail_write_callback(
                cursor, uid, ids, vals, context=context
            )
        if vals['id']:
            self.write(cursor, uid, ids, {'enviat_mail_id': vals['id']})
        return True

    _columns = {
        'enviat_mail_id': fields.many2one(
            "poweremail.mailbox",
            "E-Mail",
            readonly=True,
            ondelete="set null"
        ),
    }


GiscedataFacturacioFactura()
