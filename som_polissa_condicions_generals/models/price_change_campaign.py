# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from ast import literal_eval
import base64
import json

from osv import osv, fields

from ..price_change import (
    BANNER_CODES, LANGUAGES, required_banner_codes, validate_banner_candidates,
    validate_campaign_dates, validate_editorial_html,
)


class PriceChangePoweremail(osv.osv):
    _inherit = 'poweremail.templates'

    def get_mailbox_values(self, cursor, uid, template, record_id, context=None):
        try:
            campaign_id = self.pool.get('ir.model.data').get_object_reference(
                cursor, uid, 'som_polissa_condicions_generals',
                'price_change_campaign_template')[1]
        except ValueError:
            campaign_id = None
        ctx = dict(context or {})
        uri = '/som_polissa_condicions_generals/report/mailcanvipreus/campaign.mako'
        if (template.id == campaign_id or uri in (template.def_body_html or '')
                or uri in (template.def_body_text or '')):
            # Poweremail otherwise catches rendering errors and returns an empty
            # string, which could silently produce a mail without required text.
            ctx['raise_exception'] = True
        return super(PriceChangePoweremail, self).get_mailbox_values(
            cursor, uid, template, record_id, context=ctx)


PriceChangePoweremail()


class PriceChangeLot(osv.osv):
    _inherit = 'som.infoenergia.lot.enviament'

    _columns = {
        'price_change_selection_date': fields.date('Data selecció campanya'),
        'price_change_old_price_date': fields.date('Data preus anteriors'),
        'price_change_effective_date': fields.date('Entrada en vigor preus'),
    }


PriceChangeLot()


class PriceChangeBanner(osv.osv):
    _inherit = 'report.banner'

    def _is_editor(self, cursor, uid, context=None):
        if uid == 1:
            return False
        model_data = self.pool.get('ir.model.data')
        group_id = model_data.get_object_reference(
            cursor, uid, 'som_polissa_condicions_generals',
            'group_price_change_editor')[1]
        groups = self.pool.get('res.users').read(
            cursor, uid, uid, ['groups_id'], context=context)['groups_id']
        return group_id in groups

    def create(self, cursor, uid, vals, context=None):
        if self._is_editor(cursor, uid, context=context):
            raise osv.except_osv('Price change', 'Editors cannot create banners')
        if vals.get('code') in BANNER_CODES:
            if vals.get('image_mongo') or vals.get('image'):
                raise osv.except_osv('Price change', 'Campaign banners must be textual')
            if vals.get('html'):
                validate_editorial_html(vals['html'])
        return super(PriceChangeBanner, self).create(cursor, uid, vals, context=context)

    def write(self, cursor, uid, ids, vals, context=None):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        records = self.read(cursor, uid, ids, ['code'], context=context)
        if self._is_editor(cursor, uid, context=context):
            if set(vals) - set(['html']) or any(
                    record['code'] not in BANNER_CODES for record in records):
                raise osv.except_osv('Price change', 'Editors may only edit campaign HTML')
            if (context or {}).get('lang') not in LANGUAGES:
                raise osv.except_osv('Price change', 'Choose Catalan or Spanish')
        if vals.get('code') in BANNER_CODES or any(
                record['code'] in BANNER_CODES for record in records):
            if 'html' in vals:
                validate_editorial_html(vals['html'])
            if vals.get('image_mongo') or vals.get('image'):
                raise osv.except_osv('Price change', 'Campaign banners must be textual')
        return super(PriceChangeBanner, self).write(cursor, uid, ids, vals, context=context)

    def unlink(self, cursor, uid, ids, context=None):
        if self._is_editor(cursor, uid, context=context):
            raise osv.except_osv('Price change', 'Editors cannot delete banners')
        return super(PriceChangeBanner, self).unlink(cursor, uid, ids, context=context)


PriceChangeBanner()


class PriceChangeEnviament(osv.osv):
    _inherit = 'som.enviament.massiu'

    def create(self, cursor, uid, vals, context=None):
        if vals.get('price_change_snapshot'):
            raise osv.except_osv('Price change', 'Campaign snapshots are internal')
        return super(PriceChangeEnviament, self).create(cursor, uid, vals, context=context)

    def write(self, cursor, uid, ids, vals, context=None):
        if 'price_change_snapshot' in vals:
            raise osv.except_osv('Price change', 'Campaign snapshots are immutable')
        if set(vals).intersection(('polissa_id', 'lot_enviament')):
            record_ids = ids if isinstance(ids, (list, tuple)) else [ids]
            records = self.read(
                cursor, uid, record_ids, ['price_change_snapshot'], context=context)
            if any(record['price_change_snapshot'] for record in records):
                raise osv.except_osv(
                    'Price change', 'Create a new sending for a different campaign')
        return super(PriceChangeEnviament, self).write(cursor, uid, ids, vals, context=context)

    def copy(self, cursor, uid, record_id, default=None, context=None):
        values = dict(default or {}, price_change_snapshot=False, mail_id=False,
                      data_enviament=False, estat='obert')
        return super(PriceChangeEnviament, self).copy(
            cursor, uid, record_id, default=values, context=context)

    def _domain_matches(self, cursor, uid, record_id, domain, context=None):
        try:
            domain = literal_eval(domain) if domain else []
        except (SyntaxError, ValueError):
            raise ValueError('Invalid campaign selection domain')
        if not isinstance(domain, list):
            raise ValueError('Campaign selection domains must be lists')
        return bool(self.search(
            cursor, uid, [('id', '=', record_id)] + domain,
            context=dict(context or {}, active_test=False)))

    def _campaign_banners(self, cursor, uid, env, template_id, dates, context=None):
        domain_obj = self.pool.get('report.banner.domain')
        banner_obj = self.pool.get('report.banner')
        translation_obj = self.pool.get('ir.translation')
        domain_ids = domain_obj.search(cursor, uid, [
            ('object_ref', '=', 'poweremail.templates,{}'.format(template_id)),
        ], context=context)
        candidates = {}
        seen = set()
        for domain in domain_obj.browse(cursor, uid, domain_ids, context=context):
            if not self._domain_matches(cursor, uid, env.id, domain.domain, context=context):
                continue
            banner_ids = banner_obj.search(cursor, uid, [
                ('banner_domain_ids', 'in', [domain.id]),
                ('code', 'in', list(BANNER_CODES)),
                ('start_date', '<=', dates['selection_date']),
                '|', ('end_date', '=', False),
                ('end_date', '>=', dates['selection_date']),
            ], context=context)
            for banner in banner_obj.read(cursor, uid, banner_ids, [
                    'code', 'image_mongo'], context=context):
                if banner['id'] in seen:
                    continue
                seen.add(banner['id'])
                translation_ids = translation_obj.search(cursor, uid, [
                    ('name', '=', 'report.banner,html'), ('type', '=', 'model'),
                    ('res_id', '=', banner['id']), ('lang', 'in', list(LANGUAGES)),
                ], context=context)
                translations = translation_obj.read(
                    cursor, uid, translation_ids, ['lang', 'value'], context=context)
                banner['translations'] = {}
                for translation in translations:
                    lang = translation['lang']
                    if lang in banner['translations']:
                        raise ValueError('Duplicate campaign banner translation: {}'.format(lang))
                    banner['translations'][lang] = translation['value']
                candidates.setdefault(banner['code'], []).append(banner)
        required = required_banner_codes(
            env.polissa_id.tipus_subseccio == '21', env.polissa_id.mode_facturacio)
        return validate_banner_candidates(candidates, required)

    def _check_price_change_attachment(self, cursor, uid, record_id, context=None):
        attachment_obj = self.pool.get('ir.attachment')
        attachment_ids = attachment_obj.search(cursor, uid, [
            ('res_model', '=', 'som.enviament.massiu'), ('res_id', '=', record_id),
        ], context=context)
        if len(attachment_ids) != 1:
            raise osv.except_osv(
                'Price change',
                'The mail announces an attached contract: attach exactly one PDF first')
        attachment = attachment_obj.read(cursor, uid, attachment_ids[0],
                                         ['datas_fname', 'datas'], context=context)
        filename = attachment['datas_fname'] or ''
        if (not filename.lower().endswith('.pdf') or not attachment['datas']
                or not base64.b64decode(attachment['datas']).startswith(b'%PDF')):
            raise osv.except_osv('Price change', 'The announced contract attachment must be a PDF')
        return attachment_ids[0]

    def _get_price_change_snapshot(self, cursor, uid, record_id, template_id, context=None):
        # Read through the ORM before locking: enforce normal access checks.
        self.read(cursor, uid, record_id, ['price_change_snapshot'], context=context)
        cursor.execute(
            'SELECT price_change_snapshot FROM som_enviament_massiu '
            'WHERE id = %s FOR UPDATE', (record_id,))
        row = cursor.fetchone()
        if row and row[0]:
            snapshot = json.loads(row[0])
            if snapshot['template_id'] != template_id:
                raise osv.except_osv('Price change', 'Resend with the original campaign template')
            return snapshot
        env = self.browse(cursor, uid, record_id, context=context)
        if env.lot_enviament.email_template.id != template_id:
            raise osv.except_osv('Price change', 'Template does not match the sending batch')
        lang = env.polissa_id.titular.lang
        if lang not in LANGUAGES:
            raise osv.except_osv('Price change', 'Unsupported policy holder language')
        lot = env.lot_enviament
        try:
            dates = validate_campaign_dates({
                'selection_date': lot.price_change_selection_date,
                'old_price_date': lot.price_change_old_price_date,
                'effective_date': lot.price_change_effective_date,
            })
            banners = self._campaign_banners(
                cursor, uid, env, template_id, dates, context=context)
        except ValueError as error:
            raise osv.except_osv('Price change', str(error))
        snapshot = dict(dates, banners=banners, lang=lang, template_id=template_id)
        # Bypass the public immutable-field guard only here, in a private method.
        super(PriceChangeEnviament, self).write(cursor, uid, [record_id], {
            'price_change_snapshot': json.dumps(snapshot),
        }, context=context)
        return snapshot

    _columns = {
        'price_change_snapshot': fields.text('Campanya original', readonly=True),
    }


PriceChangeEnviament()
