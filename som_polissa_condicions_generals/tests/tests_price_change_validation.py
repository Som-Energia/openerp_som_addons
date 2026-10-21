# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import unittest

from ..price_change import (
    required_banner_codes, validate_banner_candidates, validate_campaign_dates,
    validate_editorial_html,
)


class TestPriceChangeValidation(unittest.TestCase):
    def test_explicit_dates(self):
        values = dict(selection_date='2026-08-27', old_price_date='2026-09-30',
                      effective_date='2026-10-01')
        self.assertEqual(validate_campaign_dates(values), values)
        for name in values:
            invalid = dict(values)
            invalid[name] = False
            with self.assertRaises(ValueError):
                validate_campaign_dates(invalid)
        for invalid in (
                dict(values, effective_date='2026-02-30'),
                dict(values, old_price_date='2026-10-01'),
                dict(values, selection_date='2026-10-02'),
                dict(values, selection_date='2026-8-27')):
            with self.assertRaises(ValueError):
                validate_campaign_dates(invalid)

    def test_plain_html_not_templates(self):
        content = '<p>Un canvi del 5% amb <strong>energia</strong>.</p>'
        self.assertEqual(validate_editorial_html(content), content)
        self.assertEqual(validate_editorial_html('<a href="https://somenergia.coop">Web</a>'),
                         '<a href="https://somenergia.coop">Web</a>')
        for content in (
                '', ' ', '<p><br/></p>', '${object.name}', '<% import os %>',
                '% if True:\n<p>Text</p>\n% endif', '<%include file="x"/>',
                '<script>alert(1)</script>', '<img src="https://example.org/x"/>',
                '<a href="javascript:alert(1)">Text</a>',
                '<a href="java&#115;cript:alert(1)">Text</a>',
                '<a href="//example.org">Text</a>', '<p onclick="x">Text</p>',
                '<p style="background:url(x)">Text</p>', '<iframe>Text</iframe>'):
            with self.assertRaises(ValueError):
                validate_editorial_html(content)

    def test_existing_autoconsumption_condition(self):
        for compensation in (False, True):
            for mode in ('atr', 'index'):
                codes = required_banner_codes(compensation, mode)
                self.assertIn('CANVI_PREUS_MOTIU', codes)
                self.assertIn('CANVI_PREUS_COMIAT', codes)
                self.assertEqual('CANVI_PREUS_AUTOCONSUM' in codes,
                                 compensation and mode == 'atr')

    def test_bilingual_content_missing_overlap_and_images(self):
        required = required_banner_codes(False, 'atr')
        banner = dict(translations={'ca_ES': '<p>Motiu</p>', 'es_ES': '<p>Motivo</p>'})
        candidates = dict((code, [banner]) for code in required)
        selected = validate_banner_candidates(candidates, required)
        self.assertEqual(selected[required[0]]['ca_ES'], '<p>Motiu</p>')
        for invalid in (
                {}, dict(candidates, CANVI_PREUS_MOTIU=[banner, banner]),
                dict(candidates, CANVI_PREUS_MOTIU=[dict(banner, image_mongo='image')]),
                dict(candidates, CANVI_PREUS_MOTIU=[dict(translations={'ca_ES': 'Hola'})])):
            with self.assertRaises(ValueError):
                validate_banner_candidates(invalid, required)
