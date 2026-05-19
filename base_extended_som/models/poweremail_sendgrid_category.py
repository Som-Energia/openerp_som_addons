# -*- coding: utf-8 -*-
from osv import osv, fields


class poweremail_sendgrid_category(osv.osv):
    _name = "poweremail.sendgrid.category"

    _columns = {
        "name": fields.char("Name", required=True, size=64),
    }

    def _validate_name(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            try:
                record.name.decode('ascii')
            except UnicodeDecodeError:
                return False
        return True

    _constraints = [
        (_validate_name, 'The category name must contain only ascii characters!', ['name']),
    ]

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The category name must be unique!'),
    ]


poweremail_sendgrid_category()
