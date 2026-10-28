# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import base64
import imp
import os
import subprocess
import tempfile
import unittest

from ..report import report_mailcanvipreus as pdf_module

from destral import testing
from destral.transaction import Transaction
from mock import Mock, patch
from osv import osv


class TestPriceChangeCampaign(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor, self.uid = self.txn.cursor, self.txn.user
        self.pool = self.openerp.pool
        self.env_obj = self.pool.get('som.enviament.massiu')
        self.lot_obj = self.pool.get('som.infoenergia.lot.enviament')
        self.banner_obj = self.pool.get('report.banner')
        self.translation_obj = self.pool.get('ir.translation')
        self.pol_obj = self.pool.get('giscedata.polissa')
        lang_obj = self.pool.get('res.lang')
        for code in ('ca_ES', 'es_ES'):
            lang_ids = lang_obj.search(self.cursor, self.uid, [('code', '=', code)],
                                       context={'active_test': False})
            if lang_ids:
                lang_obj.write(self.cursor, self.uid, lang_ids,
                               {'active': True, 'translatable': True,
                                'decimal_point': ',', 'thousands_sep': '.'})
            else:
                lang_obj.create(self.cursor, self.uid, {
                    'name': 'Synthetic ' + code, 'code': code,
                    'active': True, 'translatable': True,
                    'decimal_point': ',', 'thousands_sep': '.',
                })
        self.template_id = self.ref('price_change_campaign_template')
        self.pool.get('poweremail.templates').write(
            self.cursor, self.uid, [self.template_id], {'inline': False})
        self.pol_id = self.pol_obj.search(self.cursor, self.uid, [], limit=1)[0]
        pol = self.pol_obj.browse(self.cursor, self.uid, self.pol_id)
        self.pool.get('res.partner').write(
            self.cursor, self.uid, [pol.titular.id], {'lang': 'ca_ES'})
        self.lot_id = self.lot_obj.create(self.cursor, self.uid, {
            'name': 'Synthetic price-change tests', 'tipus': 'altres',
            'email_template': self.template_id, 'is_test': True,
            'price_change_selection_date': '2026-08-27',
            'price_change_old_price_date': '2026-09-30',
            'price_change_effective_date': '2026-10-01',
        })
        self.env_id = self.env_obj.create(self.cursor, self.uid, {
            'polissa_id': self.pol_id, 'lot_enviament': self.lot_id, 'estat': 'obert',
        })
        self.motiu_id = self.make_banner('CANVI_PREUS_MOTIU')
        self.make_banner('CANVI_PREUS_COMIAT')
        self.make_banner('CANVI_PREUS_AUTOCONSUM')

    def tearDown(self):
        self.txn.stop()

    def ref(self, name):
        return self.pool.get('ir.model.data').get_object_reference(
            self.cursor, self.uid, 'som_polissa_condicions_generals', name)[1]

    def make_banner(self, code, domain=None, **values):
        vals = dict(name='Synthetic ' + code, code=code, res_model='som.enviament.massiu',
                    start_date='2026-08-27', end_date='2026-08-27',
                    html='<p>Base</p>', banner_domain_ids=[
                        (6, 0, [domain or self.ref('price_change_domain_all')])])
        vals.update(values)
        banner_id = self.banner_obj.create(self.cursor, self.uid, vals)
        for lang in ('ca_ES', 'es_ES'):
            self.translation_obj._set_ids(
                self.cursor, self.uid, 'report.banner,html', 'model', lang,
                [banner_id], '<p>{} {}</p>'.format(code, lang), src='<p>Base</p>')
        return banner_id

    def snapshot(self, template_id=None):
        return self.env_obj._get_price_change_snapshot(
            self.cursor, self.uid, self.env_id, template_id or self.template_id)

    def test_explicit_dates_language_and_original_content_survive_resending(self):
        original = self.snapshot()
        self.assertEqual(original['lang'], 'ca_ES')
        self.assertEqual(original['effective_date'], '2026-10-01')
        self.banner_obj.unlink(self.cursor, self.uid, [self.motiu_id])
        self.lot_obj.write(self.cursor, self.uid, [self.lot_id], {
            'price_change_effective_date': '2027-01-01'})
        self.assertEqual(self.snapshot(), original)
        raw = self.env_obj.read(self.cursor, self.uid, self.env_id, ['price_change_snapshot'])
        self.assertEqual(json.loads(raw['price_change_snapshot']), original)

    def test_duplicate_banner_is_not_hidden_by_priority(self):
        self.make_banner('CANVI_PREUS_MOTIU', sequence=999)
        with self.assertRaises(osv.except_osv):
            self.snapshot()

    def test_missing_spanish_translation_blocks_selection(self):
        self.cursor.execute(
            'DELETE FROM ir_translation WHERE name=%s AND res_id=%s AND lang=%s',
            ('report.banner,html', self.motiu_id, 'es_ES'))
        with self.assertRaises(osv.except_osv):
            self.snapshot()

    def test_outside_inclusive_date_boundary_blocks_selection(self):
        self.banner_obj.write(self.cursor, self.uid, [self.motiu_id],
                              {'end_date': '2026-08-26'})
        with self.assertRaises(osv.except_osv):
            self.snapshot()

    def test_banners_are_isolated_by_poweremail_template(self):
        domain_obj = self.pool.get('report.banner.domain')
        other = domain_obj.create(self.cursor, self.uid, {
            'name': 'Other template', 'object_ref': 'poweremail.templates,1', 'domain': '[]',
        })
        self.make_banner('CANVI_PREUS_MOTIU', domain=other)
        self.assertEqual(self.snapshot()['template_id'], self.template_id)

    def test_domains_filter_sending_and_its_policy_not_the_policy_id(self):
        domain_obj = self.pool.get('report.banner.domain')
        domain_id = self.ref('price_change_domain_all')
        domain_obj.write(self.cursor, self.uid, [domain_id], {
            'domain': "[('polissa_id', '=', {}), ('id', '=', {})]".format(
                self.pol_id, self.env_id),
        })
        self.assertTrue(self.snapshot()['banners'])
        # Reusing a policy ID as a sending ID cannot match this predicate.
        self.assertFalse(self.env_obj._domain_matches(
            self.cursor, self.uid, self.env_id, "[('polissa_id', '=', -1)]"))

    def test_public_writes_cannot_overwrite_the_snapshot(self):
        self.snapshot()
        with self.assertRaises(osv.except_osv):
            self.env_obj.write(self.cursor, self.uid, [self.env_id],
                               {'price_change_snapshot': False})
        with self.assertRaises(osv.except_osv):
            self.env_obj.write(self.cursor, self.uid, [self.env_id],
                               {'lot_enviament': self.lot_id})

    def test_copy_requires_a_new_campaign_selection(self):
        self.snapshot()
        self.env_obj.write(self.cursor, self.uid, [self.env_id],
                           {'estat': 'enviat', 'data_enviament': '2026-08-27'})
        copied_id = self.env_obj.copy(self.cursor, self.uid, self.env_id)
        copied = self.env_obj.read(self.cursor, self.uid, copied_id,
                                   ['price_change_snapshot', 'estat', 'mail_id', 'data_enviament'])
        self.assertFalse(copied['price_change_snapshot'])
        self.assertEqual(copied['estat'], 'obert')
        self.assertFalse(copied['mail_id'])
        self.assertFalse(copied['data_enviament'])

    def test_copy_without_a_campaign_snapshot_preserves_standard_defaults(self):
        self.lot_obj.write(self.cursor, self.uid, [self.lot_id], {
            'email_template': self.ref('canviPreusBackend')})
        defaults = {'estat': 'enviat', 'data_enviament': '2026-08-27'}
        copied_id = self.env_obj.copy(
            self.cursor, self.uid, self.env_id, default=defaults)
        copied = self.env_obj.read(
            self.cursor, self.uid, copied_id,
            ['price_change_snapshot', 'estat', 'data_enviament'])
        self.assertFalse(copied['price_change_snapshot'])
        self.assertEqual(copied['estat'], 'enviat')
        self.assertEqual(copied['data_enviament'], '2026-08-27')
        self.assertEqual(defaults, {'estat': 'enviat', 'data_enviament': '2026-08-27'})

    def test_backend_delegates_policy_with_explicit_dates_and_template_context(self):
        backend = self.pool.get('report.backend.mailcanvipreus')
        pdf_backend = self.pool.get('report.backend.mailcanvipreus.pdf')
        env = self.env_obj.browse(self.cursor, self.uid, self.env_id)
        with patch.object(backend, 'browsify_record', return_value=env):
            with patch.object(pdf_backend, 'get_data',
                              return_value={'numeric': 12.345, 'modcon': 'index'}) as get_data:
                result = backend.get_campaign_data(self.cursor, self.uid, self.env_id, context={
                    'avoid_formatting': True, 'pem_template_id': self.template_id})
        self.assertEqual(result['numeric'], 12.345)
        args, kwargs = get_data.call_args
        self.assertEqual(args[2], self.pol_id)
        self.assertEqual(kwargs['context']['lang'], 'ca_ES')
        self.assertEqual(kwargs['context']['price_change_old_price_date'], '2026-09-30')
        self.assertEqual(kwargs['context']['price_change_effective_date'], '2026-10-01')

    def test_resending_with_a_different_template_is_rejected(self):
        self.snapshot()
        with self.assertRaises(osv.except_osv):
            self.snapshot(template_id=self.template_id + 10000)

    def make_editor(self):
        base_group = self.pool.get('ir.model.data').get_object_reference(
            self.cursor, self.uid, 'base', 'group_user')[1]
        return self.pool.get('res.users').create(self.cursor, self.uid, {
            'name': 'Synthetic editorial user', 'login': 'synthetic-price-editor',
            'groups_id': [(6, 0, [base_group, self.ref('group_price_change_editor')])],
        })

    def test_editor_can_change_only_campaign_banner_html(self):
        editor_id = self.make_editor()
        self.banner_obj.write(self.cursor, editor_id, [self.motiu_id],
                              {'html': '<p>Nou motiu</p>'}, context={'lang': 'ca_ES'})
        for values in ({'code': 'OTHER'}, {'sequence': 999},
                       {'html': '${object.name}'}, {'image_mongo': 'image'}):
            with self.assertRaises((osv.except_osv, ValueError)):
                self.banner_obj.write(self.cursor, editor_id, [self.motiu_id],
                                      values, context={'lang': 'ca_ES'})
        with self.assertRaises(osv.except_osv):
            self.banner_obj.unlink(self.cursor, editor_id, [self.motiu_id])

    def test_editor_membership_does_not_restrict_other_models_translations(self):
        editor_id = self.make_editor()
        translation_id = self.translation_obj.create(self.cursor, editor_id, {
            'name': 'poweremail.templates,def_body_html', 'type': 'model',
            'res_id': self.template_id, 'lang': 'ca_ES', 'value': '<p>Original</p>',
        })
        self.translation_obj.write(self.cursor, editor_id, [translation_id], {
            'value': '<p>Updated</p>'})
        translation = self.translation_obj.read(
            self.cursor, editor_id, translation_id, ['value'])
        self.assertEqual(translation['value'], '<p>Updated</p>')
        self.translation_obj.unlink(self.cursor, editor_id, [translation_id])
        self.assertFalse(self.translation_obj.search(
            self.cursor, editor_id, [('id', '=', translation_id)]))

    def render_data(self):
        prices = {'te': {'P1': 0.123, 'P2': 0.101, 'P3': 0.099},
                  'tp': {'P1': 30.0, 'P2': 4.0}}
        data = dict(lang='ca_ES', nom_titular=' Ada,', codi_polissa='SYNTHETIC',
                    modcon=False, tarifa_acces='2.0TD', mode_facturacio='atr',
                    impostos_str='IVA del 21%', impost_electric_str='5,11%',
                    te_gkwh=False, autoconsum={'compensacio': False},
                    origen='pdf', consum_total=1000, potencia=3.0,
                    preu_vell=350.0, preu_nou=340.0,
                    preu_vell_imp=445.0, preu_nou_imp=432.0)
        for key in ('preus_antics', 'preus_nous', 'preus_antics_imp', 'preus_nous_imp'):
            data[key] = prices
        return data

    def mailbox_values(self, template_id=None):
        templates = self.pool.get('poweremail.templates')
        template = templates.browse(self.cursor, self.uid, template_id or self.template_id)
        account = {'id': 1, 'name': 'Synthetic account', 'email_id': 'test@example.invalid'}
        with patch.object(templates, 'get_from_account_id_from_template', return_value=account):
            return templates.get_mailbox_values(
                self.cursor, self.uid, template, self.env_id, context={})

    def add_contract_attachment(self):
        return self.pool.get('ir.attachment').create(self.cursor, self.uid, {
            'name': 'Synthetic contract', 'datas_fname': 'synthetic-contract.pdf',
            'datas': base64.b64encode(b'%PDF-1.4\nsynthetic contract fixture\n'),
            'res_model': 'som.enviament.massiu', 'res_id': self.env_id,
        })

    def test_real_poweremail_renderer_uses_campaign_content_and_dynamic_subject(self):
        self.add_contract_attachment()
        pdf_backend = self.pool.get('report.backend.mailcanvipreus.pdf')
        with patch.object(pdf_backend, 'get_data', return_value=self.render_data()):
            values = self.mailbox_values()
        self.assertIn('2026-10-01', values['pem_subject'])
        self.assertIn('CANVI_PREUS_MOTIU ca_ES', values['pem_body_html'])
        self.assertIn('0,123', values['pem_body_html'])
        self.assertIn('HEADER', values['pem_body_html'])
        self.assertFalse(values['pem_cc'])
        self.assertFalse(values['pem_bcc'])

    def test_poweremail_does_not_silence_missing_required_content(self):
        self.banner_obj.unlink(self.cursor, self.uid, [self.motiu_id])
        with self.assertRaises(osv.except_osv):
            self.mailbox_values()

    def test_mail_cannot_announce_a_contract_that_is_not_attached(self):
        pdf_backend = self.pool.get('report.backend.mailcanvipreus.pdf')
        with patch.object(pdf_backend, 'get_data', return_value=self.render_data()):
            with self.assertRaises(osv.except_osv):
                self.mailbox_values()
        attachment_id = self.add_contract_attachment()
        self.assertEqual(self.env_obj._check_price_change_attachment(
            self.cursor, self.uid, self.env_id), attachment_id)
        self.pool.get('ir.attachment').write(self.cursor, self.uid, [attachment_id],
                                             {'datas_fname': 'not-a-contract.txt'})
        with self.assertRaises(osv.except_osv):
            self.env_obj._check_price_change_attachment(self.cursor, self.uid, self.env_id)

    def test_copied_campaign_templates_fail_closed_without_their_own_banners(self):
        templates = self.pool.get('poweremail.templates')
        copied = templates.copy(self.cursor, self.uid, self.template_id,
                                default={'name': 'Synthetic copied campaign'})
        self.lot_obj.write(self.cursor, self.uid, [self.lot_id], {'email_template': copied})
        with self.assertRaises(osv.except_osv):
            self.mailbox_values(template_id=copied)

    def test_duplicate_translations_are_not_selected_arbitrarily(self):
        self.translation_obj.create(self.cursor, self.uid, {
            'name': 'report.banner,html', 'type': 'model', 'res_id': self.motiu_id,
            'lang': 'ca_ES', 'value': '<p>Duplicate</p>',
        })
        with self.assertRaises(osv.except_osv):
            self.snapshot()

    def test_pdf_does_not_treat_a_policy_id_as_a_sending_id(self):
        report = pdf_module.MailCanviPreusReport('report.price_change_pdf_test')
        pol = self.pol_obj.browse(self.cursor, self.uid, self.pol_id)
        self.env_obj.create(self.cursor, self.uid, {
            'polissa_id': self.pol_id, 'lot_enviament': self.lot_id, 'estat': 'obert'})
        with self.assertRaises(ValueError):
            report._render_record(self.cursor, self.uid, self.pool, pol, {})
        with self.assertRaises(ValueError):
            report._render_record(self.cursor, self.uid, self.pool, Mock(id=-1),
                                  {'price_change_enviament_id': self.env_id})
        with self.assertRaises(ValueError):
            report.create(self.cursor, self.uid, [self.pol_id, self.pol_id], {},
                          {'price_change_enviament_id': self.env_id})

    @unittest.skipUnless(os.environ.get('SOM_PRICE_CHANGE_PDF_SMOKE'),
                         'Opt in to the real Chromium/Puppeteer smoke test')
    def test_real_pdf_renderer_shares_the_poweremail_html_contract(self):
        self.add_contract_attachment()
        pdf_backend = self.pool.get('report.backend.mailcanvipreus.pdf')
        report = pdf_module.MailCanviPreusReport('report.price_change_real_pdf_test')
        captured = []
        write_file = pdf_module.ReportParser.write_temporal_file

        def capture_html(content, extension):
            captured.append(content)
            return write_file(content, extension)

        with patch.object(pdf_backend, 'get_data', return_value=self.render_data()):
            values = self.mailbox_values()
            with patch.object(pdf_module.ReportParser, 'write_temporal_file',
                              side_effect=capture_html):
                documents, filetype = report.create(
                    self.cursor, self.uid, [self.pol_id], {},
                    {'price_change_enviament_id': self.env_id})
        self.assertEqual(captured, [values['pem_body_html']])
        self.assertEqual(filetype, 'pdf')
        pdf = base64.b64decode(documents[0])
        self.assertTrue(pdf.startswith(b'%PDF'))
        with tempfile.NamedTemporaryFile(suffix='.pdf') as document:
            document.write(pdf)
            document.flush()
            text = subprocess.check_output(['pdftotext', document.name, '-']).decode('utf-8')
        self.assertIn('2026-10-01', text)
        self.assertIn('CANVI_PREUS_MOTIU', text)
        self.assertIn('CNMC', text)

    def test_migration_is_idempotent_and_does_not_overwrite_noupdate_templates(self):
        templates = self.pool.get('poweremail.templates')
        legacy_id = self.ref('canviPreusBackend')
        legacy_before = templates.read(self.cursor, self.uid, legacy_id,
                                       ['def_subject', 'def_body_html'])
        templates.write(self.cursor, self.uid, [self.template_id],
                        {'def_subject': 'SYNTHETIC REVIEWED SUBJECT'})
        path = os.path.join(os.path.dirname(__file__), '..', 'migrations',
                            '5.0.25.5.0', 'post-0003_add_price_change_campaign.py')
        migration = imp.load_source('price_change_migration_test', path)
        migration.up(self.cursor, '5.0.25.5.0')
        migration.up(self.cursor, '5.0.25.5.0')
        subject = templates.read(self.cursor, self.uid, self.template_id,
                                 ['def_subject'])['def_subject']
        self.assertEqual(subject, 'SYNTHETIC REVIEWED SUBJECT')
        legacy_after = templates.read(self.cursor, self.uid, legacy_id,
                                      ['def_subject', 'def_body_html'])
        self.assertEqual(legacy_after, legacy_before)

    def test_created_executable_translation_blocks_campaign_not_core_storage(self):
        translation_ids = self.translation_obj.search(self.cursor, self.uid, [
            ('name', '=', 'report.banner,html'), ('type', '=', 'model'),
            ('res_id', '=', self.motiu_id), ('lang', '=', 'es_ES'),
        ])
        self.translation_obj.unlink(self.cursor, self.uid, translation_ids)
        translation_id = self.translation_obj.create(self.cursor, self.uid, {
            'name': 'report.banner,html', 'type': 'model',
            'res_id': self.motiu_id, 'lang': 'es_ES', 'value': '${object.name}',
        })
        self.assertTrue(translation_id)
        with self.assertRaises(osv.except_osv):
            self.snapshot()
        with self.assertRaises(osv.except_osv):
            self.mailbox_values()
        self.assertFalse(self.env_obj.read(
            self.cursor, self.uid, self.env_id,
            ['price_change_snapshot'])['price_change_snapshot'])

    def test_updated_invalid_translation_blocks_campaign_rendering(self):
        translation_ids = self.translation_obj.search(self.cursor, self.uid, [
            ('name', '=', 'report.banner,html'), ('type', '=', 'model'),
            ('res_id', '=', self.motiu_id), ('lang', '=', 'es_ES'),
        ])
        for content in ('${object.name}', '<script>alert(1)</script>', ''):
            self.translation_obj.write(self.cursor, self.uid, translation_ids,
                                       {'value': content})
            with self.assertRaises(osv.except_osv):
                self.mailbox_values()
            self.assertFalse(self.env_obj.read(
                self.cursor, self.uid, self.env_id,
                ['price_change_snapshot'])['price_change_snapshot'])
