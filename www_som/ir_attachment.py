# -*- coding: utf-8 -*-

from osv import osv, fields


class IrAttachmentCategory(osv.osv):
    _inherit = 'ir.attachment.category'

    _columns = {
        'ov_available': fields.boolean('Disponible a la OV',
            help='Els adjunts dins d\'aquesta categoria es podran consultar desde la OV'),
    }

    _defaults = {
        'ov_available': lambda *a: False
    }


IrAttachmentCategory()