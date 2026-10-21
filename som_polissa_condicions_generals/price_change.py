# -*- coding: utf-8 -*-
"""Validation shared by the ORM and the price-change rendering tests.

Editorial strings are never compiled as Mako templates.
"""
from __future__ import absolute_import, unicode_literals

from datetime import datetime
import re

from lxml import html


LANGUAGES = ('ca_ES', 'es_ES')
BANNER_CODES = (
    'CANVI_PREUS_MOTIU', 'CANVI_PREUS_AUTOCONSUM', 'CANVI_PREUS_COMIAT',
)
DATE_FIELDS = ('selection_date', 'old_price_date', 'effective_date')
_ALLOWED_TAGS = frozenset((
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'a', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'blockquote', 'span', 'div',
))
_ALLOWED_ATTRIBUTES = frozenset(('href', 'title', 'target', 'rel'))
_MAKO = re.compile(r'\$\{|<%|%>|^\s*[%#]', re.MULTILINE)


def validate_editorial_html(content):
    if not content or not content.strip():
        raise ValueError('Empty price-change editorial content')
    if _MAKO.search(content):
        raise ValueError('Executable template syntax is not allowed')
    root = html.fragment_fromstring(content, create_parent='div')
    if not ''.join(root.itertext()).strip():
        raise ValueError('Empty price-change editorial content')
    for element in root.iter():
        if element.tag not in _ALLOWED_TAGS:
            raise ValueError('Unsupported editorial HTML element')
        for attribute, value in element.attrib.items():
            if attribute not in _ALLOWED_ATTRIBUTES:
                raise ValueError('Unsupported editorial HTML attribute')
            if attribute == 'href':
                # An allowlist also rejects entity-encoded executable schemes,
                # whitespace-obfuscated URLs and protocol-relative URLs.
                if not value.lower().startswith(('https://', 'http://', 'mailto:')):
                    raise ValueError('Unsupported editorial link protocol')
            if attribute == 'target' and value not in ('_blank', '_self'):
                raise ValueError('Unsupported editorial link target')
    return content


def validate_campaign_dates(values):
    result = {}
    for name in DATE_FIELDS:
        value = values.get(name)
        if not value:
            raise ValueError('Missing campaign date: {}'.format(name))
        parsed = datetime.strptime(value, '%Y-%m-%d')
        if parsed.strftime('%Y-%m-%d') != value:
            raise ValueError('Campaign dates must use YYYY-MM-DD')
        result[name] = value
    if result['old_price_date'] >= result['effective_date']:
        raise ValueError('Old prices must precede the effective date')
    if result['selection_date'] > result['effective_date']:
        raise ValueError('Campaign selection must not follow the effective date')
    return result


def required_banner_codes(compensation, billing_mode):
    result = ['CANVI_PREUS_MOTIU', 'CANVI_PREUS_COMIAT']
    if compensation and billing_mode == 'atr':
        result.append('CANVI_PREUS_AUTOCONSUM')
    return result


def validate_banner_candidates(candidates, required):
    """Candidates have already passed template, date and record domains."""
    selected = {}
    for code in required:
        matches = candidates.get(code, [])
        if len(matches) != 1:
            raise ValueError('Expected one banner for {}, found {}'.format(code, len(matches)))
        banner = matches[0]
        if banner.get('image_mongo'):
            raise ValueError('Price-change banners must not contain images')
        translations = banner.get('translations', {})
        selected[code] = {}
        for lang in LANGUAGES:
            selected[code][lang] = validate_editorial_html(translations.get(lang))
    return selected
