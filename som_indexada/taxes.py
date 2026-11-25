# -*- coding: utf-8 -*-
from __future__ import absolute_import, division


def get_tax_polissa(cursor, uid, pol_obj, polissa_id, context=None):
    context = dict(context or {})
    if context.get('date') and hasattr(context['date'], 'strftime'):
        context['date'] = context['date'].strftime('%Y-%m-%d')
    state = pol_obj.read(cursor, uid, polissa_id, ['state'], context={})['state']
    return pol_obj.browse(
        cursor, uid, polissa_id, context={} if state == 'esborrany' else context
    )


def get_mapped_taxes(cursor, uid, pol, taxes=None, context=None):
    """Map energy defaults (or a product's taxes) through the contract."""
    tax_obj = pol.pool.get('account.tax')
    if taxes is None:
        conf_obj = pol.pool.get('res.config')
        tax_ids = [
            int(conf_obj.get(cursor, uid, 'default_iva_21_tax_id')),
            int(conf_obj.get(cursor, uid, 'default_iese_tax_id')),
        ]
        taxes = tax_obj.browse(cursor, uid, tax_ids, context=context)
    fiscal_position = pol.fiscal_position_id or pol.titular.property_account_position
    if context and 'force_fiscal_position' in context:
        fp_id = context['force_fiscal_position']
        fiscal_position = pol.pool.get('account.fiscal.position').browse(
            cursor, uid, fp_id, context=context
        ) if fp_id else False
    tax_ids = pol.pool.get('account.fiscal.position').map_tax(
        cursor, uid, fiscal_position, taxes, context=context
    )
    return tax_obj.browse(cursor, uid, tax_ids, context=context)


def get_simplified_taxes(cursor, uid, pol_obj, polissa_id, context=None):
    """Keep the report API while sharing fiscal-position lookup."""
    context = dict(context or {})
    if context.get('date') and hasattr(context['date'], 'strftime'):
        context['date'] = context['date'].strftime('%Y-%m-%d')
    pol = get_tax_polissa(cursor, uid, pol_obj, polissa_id, context=context)
    taxes = get_mapped_taxes(cursor, uid, pol, context=context)
    result = {}
    for tax in taxes:
        if 'IVA' in tax.name:
            result['IVA'] = 0.1 if context.get('iva10') else tax.amount
        elif 'IGIC' in tax.name:
            result['IGIC'] = tax.amount
        else:
            result['IE'] = tax.amount
    return result


def compute_estimation_taxes(cursor, uid, pol, amount, taxes=None, context=None, product=None):
    """Use the ERP engine: IE can be code-based and carry exemption factors."""
    mapped = get_mapped_taxes(cursor, uid, pol, taxes=taxes, context=context)
    line_taxes = []
    for tax in mapped:
        line_taxes.extend(tax.child_ids if tax.child_depend else [tax])
    base = amount
    total = amount
    rates = {}
    for tax in sorted(line_taxes, key=lambda item: item.sequence):
        # account_tax_factor applies the factor to the base before computing.
        computed = pol.pool.get('account.tax').compute(
            cursor, uid, [tax], base * tax.factor, 1,
            address_id=pol.direccio_pagament.id,
            partner=pol.titular, product=product, context=context
        )
        tax_amount = sum(item['amount'] for item in computed)
        key = 'IGIC' if 'IGIC' in tax.name else 'IVA' if 'IVA' in tax.name else 'IE'
        rates[key] = rates.get(key, 0) + (tax_amount / base if base else 0)
        total += tax_amount
        if tax.include_base_amount:
            base += tax_amount
    return total, rates
