# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from datetime import date, timedelta
import base64
import imp
import os
import subprocess
import tempfile
import unittest

from destral import testing
from destral.transaction import Transaction
from mock import Mock, patch

from .. import report_backend_mailcanvipreus as backend_module
from ..report import report_mailcanvipreus as pdf_module


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
        self.backend = self.pool.get('report.backend.mailcanvipreus')
        self.pdf_backend = self.pool.get('report.backend.mailcanvipreus.pdf')
        self.today = date.today().strftime('%Y-%m-%d')
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
        self.partner_id = pol.titular.id
        self.pool.get('res.partner').write(
            self.cursor, self.uid, [self.partner_id], {'lang': 'ca_ES'})
        self.lot_id = self.lot_obj.create(self.cursor, self.uid, {
            'name': 'Synthetic price-change tests', 'tipus': 'altres',
            'email_template': self.template_id, 'is_test': True,
        })
        self.env_id = self.env_obj.create(self.cursor, self.uid, {
            'polissa_id': self.pol_id, 'lot_enviament': self.lot_id, 'estat': 'obert',
        })
        self.motiu_id = self.make_banner('CANVI_PREUS_MOTIU')
        self.make_banner('CANVI_PREUS_COMIAT')
        self.make_banner('CANVI_PREUS_AUTOCONSUM')

    def tearDown(self):
        self.txn.stop()

    def ref(self, name, module='som_polissa_condicions_generals'):
        return self.pool.get('ir.model.data').get_object_reference(
            self.cursor, self.uid, module, name)[1]

    def make_banner(self, code, domain=None, **values):
        vals = dict(name='Synthetic ' + code, code=code, res_model='som.enviament.massiu',
                    start_date=self.today, end_date=self.today,
                    html='<p>Base</p>', banner_domain_ids=[
                        (6, 0, [domain or self.ref('price_change_domain_all')])])
        vals.update(values)
        banner_id = self.banner_obj.create(self.cursor, self.uid, vals)
        for lang in ('ca_ES', 'es_ES'):
            self.translation_obj._set_ids(
                self.cursor, self.uid, 'report.banner,html', 'model', lang,
                [banner_id], '<p>{} {}</p>'.format(code, lang), src='<p>Base</p>')
        return banner_id

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

    def campaign_data(self, context=None):
        ctx = dict(context or {}, pem_template_id=self.template_id, avoid_formatting=True)
        with patch.object(self.pdf_backend, 'get_data', return_value=self.render_data()):
            return self.backend.get_campaign_data(
                self.cursor, self.uid, self.env_id, context=ctx)

    def mailbox_values(self, context=None):
        templates = self.pool.get('poweremail.templates')
        template = templates.browse(self.cursor, self.uid, self.template_id)
        account = {'id': 1, 'name': 'Synthetic account', 'email_id': 'test@example.invalid'}
        with patch.object(templates, 'get_from_account_id_from_template', return_value=account):
            with patch.object(self.pdf_backend, 'get_data', return_value=self.render_data()):
                return templates.get_mailbox_values(
                    self.cursor, self.uid, template, self.env_id, context=context or {})

    def test_shared_models_have_no_campaign_fields(self):
        lot_fields = self.lot_obj.fields_get(self.cursor, self.uid)
        for name in ('price_change_selection_date', 'price_change_old_price_date',
                     'price_change_effective_date'):
            self.assertNotIn(name, lot_fields)
        self.assertNotIn('price_change_snapshot', self.env_obj.fields_get(self.cursor, self.uid))

    def test_existing_banner_resolver_uses_today_template_and_sending(self):
        original_context = {'pem_template_id': self.template_id, 'avoid_formatting': True,
                            'price_change_selection_date': '2099-01-01'}
        banners = dict((code, '<p>Text</p>') for code in (
            'CANVI_PREUS_MOTIU', 'CANVI_PREUS_COMIAT', 'CANVI_PREUS_AUTOCONSUM'))
        with patch.object(self.banner_obj, 'get_report_banners', return_value=banners) as resolve:
            with patch.object(self.pdf_backend, 'get_data',
                              return_value=self.render_data()) as calculate:
                result = self.backend.get_campaign_data(
                    self.cursor, self.uid, self.env_id, context=original_context)
        args, kwargs = resolve.call_args
        self.assertEqual(args[2:], (
            'poweremail.templates,{}'.format(self.template_id), self.today, self.env_id))
        self.assertEqual(kwargs['context']['lang'], 'ca_ES')
        self.assertEqual(result['campaign']['selection_date'], self.today)
        self.assertEqual(result['campaign']['old_price_date'], self.today)
        self.assertEqual(calculate.call_args[0][2], self.pol_id)
        self.assertEqual(calculate.call_args[1]['context']['price_change_old_price_date'],
                         self.today)
        self.assertEqual(original_context['price_change_selection_date'], '2099-01-01')
        self.assertNotIn('lang', original_context)

    def test_effective_date_uses_existing_pricelist_resolution_for_subject_and_body(self):
        with patch.object(self.pdf_backend, 'get_price_change_date', return_value='2099-12-31'):
            data = self.campaign_data()
            subject = self.backend.get_campaign_subject(self.cursor, self.uid, self.env_id)
        self.assertEqual(data['campaign']['effective_date'], '2099-12-31')
        self.assertIn('2099-12-31', subject)

    def test_standard_banners_are_translated_for_the_policy_holder(self):
        self.pool.get('res.partner').write(
            self.cursor, self.uid, [self.partner_id], {'lang': 'es_ES'})
        result = self.campaign_data()
        self.assertEqual(result['lang'], 'es_ES')
        self.assertEqual(result['banners']['CANVI_PREUS_MOTIU'],
                         '<p>CANVI_PREUS_MOTIU es_ES</p>')
        self.assertEqual(self.backend.get_lang(self.cursor, self.uid, self.env_id), 'es_ES')

    def test_standard_translation_fallback_is_preserved(self):
        self.pool.get('res.partner').write(
            self.cursor, self.uid, [self.partner_id], {'lang': 'es_ES'})
        translation_ids = self.translation_obj.search(self.cursor, self.uid, [
            ('name', '=', 'report.banner,html'), ('res_id', '=', self.motiu_id),
            ('lang', '=', 'es_ES'),
        ])
        self.translation_obj.unlink(self.cursor, self.uid, translation_ids)
        self.assertEqual(self.campaign_data()['banners']['CANVI_PREUS_MOTIU'], '<p>Base</p>')

    def test_standard_banner_sequence_is_not_replaced_by_overlap_restrictions(self):
        priority_id = self.make_banner('CANVI_PREUS_MOTIU', sequence=-1)
        self.banner_obj.write(self.cursor, self.uid, [priority_id],
                              {'html': '<p>Priority</p>'}, context={'lang': 'ca_ES'})
        self.assertEqual(self.campaign_data()['banners']['CANVI_PREUS_MOTIU'], '<p>Priority</p>')

    def test_domains_filter_the_sending_and_its_policy(self):
        domain_obj = self.pool.get('report.banner.domain')
        domain_id = self.ref('price_change_domain_all')
        domain_obj.write(self.cursor, self.uid, [domain_id], {
            'domain': "[('polissa_id', '=', {}), ('id', '=', {})]".format(
                self.pol_id, self.env_id),
        })
        self.assertIn('CANVI_PREUS_MOTIU', self.campaign_data()['banners'])
        domain_obj.write(self.cursor, self.uid, [domain_id], {
            'domain': "[('polissa_id', '=', -1)]"})
        with self.assertRaises(ValueError):
            self.campaign_data()

    def test_banners_are_isolated_by_template(self):
        templates = self.pool.get('poweremail.templates')
        copied = templates.copy(self.cursor, self.uid, self.template_id,
                                default={'name': 'Synthetic copied campaign'})
        with patch.object(self.pdf_backend, 'get_data', return_value=self.render_data()):
            with self.assertRaises(ValueError):
                self.backend.get_campaign_data(self.cursor, self.uid, self.env_id, context={
                    'pem_template_id': copied, 'avoid_formatting': True})

    def test_expired_banner_is_not_selected(self):
        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.banner_obj.write(self.cursor, self.uid, [self.motiu_id], {'end_date': yesterday})
        with self.assertRaises(ValueError):
            self.campaign_data()

    def test_each_render_reads_current_banners_without_a_snapshot(self):
        self.assertIn('CANVI_PREUS_MOTIU', self.campaign_data()['banners']['CANVI_PREUS_MOTIU'])
        self.banner_obj.write(self.cursor, self.uid, [self.motiu_id],
                              {'html': '<p>Updated</p>'}, context={'lang': 'ca_ES'})
        self.assertEqual(self.campaign_data()['banners']['CANVI_PREUS_MOTIU'], '<p>Updated</p>')
        tomorrow = date.today() + timedelta(days=1)
        with patch.object(backend_module, 'date') as clock:
            clock.today.return_value = tomorrow
            with self.assertRaises(ValueError):
                self.campaign_data()

    def test_rendering_does_not_write_to_the_lot_or_sending(self):
        lot_fields = ['name', 'email_template', 'write_date']
        sending_fields = ['polissa_id', 'lot_enviament', 'estat', 'mail_id',
                          'data_enviament', 'write_date']
        lot_before = self.lot_obj.read(self.cursor, self.uid, self.lot_id, lot_fields)
        sending_before = self.env_obj.read(self.cursor, self.uid, self.env_id, sending_fields)
        self.campaign_data()
        self.backend.get_campaign_subject(self.cursor, self.uid, self.env_id)
        self.assertEqual(self.lot_obj.read(self.cursor, self.uid, self.lot_id, lot_fields),
                         lot_before)
        self.assertEqual(self.env_obj.read(self.cursor, self.uid, self.env_id, sending_fields),
                         sending_before)

    def test_standard_banner_manager_permissions_are_unchanged(self):
        user_id = self.pool.get('res.users').create(self.cursor, self.uid, {
            'name': 'Synthetic banner manager', 'login': 'synthetic-banner-manager',
            'groups_id': [(6, 0, [self.ref('group_user', 'base'),
                                  self.ref('group_banner_manager', 'report_banner')])],
        })
        banner_id = self.banner_obj.create(self.cursor, user_id, {
            'name': 'Synthetic unrestricted banner', 'code': 'CANVI_PREUS_MOTIU',
            'res_model': 'som.enviament.massiu', 'start_date': self.today,
            'html': '<p style="color:red">Text</p>',
        })
        self.banner_obj.write(self.cursor, user_id, [banner_id], {
            'code': 'OTHER', 'sequence': 999, 'html': '${object.name}'})
        self.banner_obj.unlink(self.cursor, user_id, [banner_id])
        self.assertFalse(self.banner_obj.search(self.cursor, user_id, [('id', '=', banner_id)]))

    def test_banner_html_has_no_new_restrictions_and_is_not_executed_as_mako(self):
        content = '<p style="color:red">${1 / 0}</p>'
        self.banner_obj.write(self.cursor, self.uid, [self.motiu_id],
                              {'html': content}, context={'lang': 'ca_ES'})
        self.assertIn(content, self.mailbox_values()['pem_body_html'])

    def test_standard_sending_copy_preserves_defaults(self):
        copied_id = self.env_obj.copy(self.cursor, self.uid, self.env_id, default={
            'estat': 'enviat', 'data_enviament': self.today})
        copied = self.env_obj.read(self.cursor, self.uid, copied_id, ['estat', 'data_enviament'])
        self.assertEqual(copied['estat'], 'enviat')
        self.assertEqual(copied['data_enviament'], self.today)

    def test_poweremail_retains_its_existing_error_handling(self):
        self.banner_obj.unlink(self.cursor, self.uid, [self.motiu_id])
        self.assertFalse(self.mailbox_values()['pem_body_html'])
        with self.assertRaises(ValueError):
            self.mailbox_values(context={'raise_exception': True})

    def test_real_poweremail_renderer_uses_current_content_and_dynamic_subject(self):
        with patch.object(self.pdf_backend, 'get_price_change_date', return_value='2099-12-31'):
            values = self.mailbox_values()
        self.assertIn('2099-12-31', values['pem_subject'])
        self.assertIn(self.today, values['pem_body_html'])
        self.assertIn('CANVI_PREUS_MOTIU ca_ES', values['pem_body_html'])
        self.assertIn('0,123', values['pem_body_html'])
        self.assertIn('HEADER', values['pem_body_html'])
        self.assertFalse(values['pem_cc'])
        self.assertFalse(values['pem_bcc'])

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

    @unittest.skipUnless(os.environ.get('SOM_PRICE_CHANGE_PDF_SMOKE'),
                         'Opt in to the real Chromium/Puppeteer smoke test')
    def test_real_pdf_renderer_shares_the_poweremail_html_contract(self):
        report = pdf_module.MailCanviPreusReport('report.price_change_real_pdf_test')
        captured = []
        write_file = pdf_module.ReportParser.write_temporal_file

        def capture_html(content, extension):
            captured.append(content)
            return write_file(content, extension)

        with patch.object(self.pdf_backend, 'get_data', return_value=self.render_data()):
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
        self.assertIn(self.today, text)
        self.assertIn('CANVI_PREUS_MOTIU', text)
        self.assertIn('CNMC', text)

    def test_migration_is_idempotent_and_preserves_noupdate_templates(self):
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
        self.assertEqual(templates.read(self.cursor, self.uid, self.template_id,
                                        ['def_subject'])['def_subject'],
                         'SYNTHETIC REVIEWED SUBJECT')
        self.assertEqual(templates.read(self.cursor, self.uid, legacy_id,
                                        ['def_subject', 'def_body_html']), legacy_before)
