# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from osv import osv

from ..price_change import BANNER_CODES, LANGUAGES, validate_editorial_html


class PriceChangeTranslation(osv.osv):
    _inherit = 'ir.translation'

    def _check_campaign_translation(self, cursor, uid, values, context=None):
        banner_obj = self.pool.get('report.banner')
        is_editor = banner_obj._is_editor(cursor, uid, context=context)
        is_banner = (values.get('name') == 'report.banner,html'
                     and values.get('type') == 'model' and values.get('res_id'))
        is_campaign = False
        if is_banner:
            banner = banner_obj.read(cursor, uid, values['res_id'], ['code'], context=context)
            is_campaign = banner['code'] in BANNER_CODES
        if is_editor and (not is_campaign or values.get('lang') not in LANGUAGES):
            raise osv.except_osv('Price change', 'Editors may only translate campaign HTML')
        if is_campaign:
            validate_editorial_html(values.get('value'))

    def create(self, cursor, uid, vals, context=None):
        self._check_campaign_translation(cursor, uid, vals, context=context)
        return super(PriceChangeTranslation, self).create(cursor, uid, vals, context=context)

    def write(self, cursor, uid, ids, vals, context=None):
        record_ids = ids if isinstance(ids, (list, tuple)) else [ids]
        for record in self.read(cursor, uid, record_ids, [
                'name', 'type', 'res_id', 'lang', 'value'], context=context):
            if self.pool.get('report.banner')._is_editor(cursor, uid, context=context):
                if set(vals) - set(['value']):
                    raise osv.except_osv('Price change', 'Editors may only edit translation values')
            record.update(vals)
            self._check_campaign_translation(cursor, uid, record, context=context)
        return super(PriceChangeTranslation, self).write(cursor, uid, ids, vals, context=context)

    def unlink(self, cursor, uid, ids, context=None):
        if self.pool.get('report.banner')._is_editor(cursor, uid, context=context):
            raise osv.except_osv('Price change', 'Editors cannot delete translations')
        return super(PriceChangeTranslation, self).unlink(cursor, uid, ids, context=context)


PriceChangeTranslation()
