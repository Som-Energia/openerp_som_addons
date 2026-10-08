# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import argparse
import csv
import sys
from collections import Counter

from erppeek import Client
from stdnum import es

import dbconfig

text_type = type(u'')


BONO_SOCIAL_MODULE = 'giscedata_facturacio_comer_bono_social'
BONO_SOCIAL_XMLID = 'bono_social_pending_state_process'


def is_enterprise_vat(vat):
    """Mirror res.partner.is_enterprise_vat() in the ERP."""
    if not vat:
        return False

    country_code = len(vat) >= 2 and vat[:2]
    if country_code == 'ES':
        return es.cif.is_valid(vat[2:])
    return False


def many2one_id(value):
    return value and value[0] or False


def get_bono_social_process_id(erp):
    imd = erp.model('ir.model.data')
    xmlids = imd.search([
        ('module', '=', BONO_SOCIAL_MODULE),
        ('name', '=', BONO_SOCIAL_XMLID),
    ])
    if len(xmlids) != 1:
        raise RuntimeError(
            'No s’ha pogut resoldre l’XML ID del procés Bo Social: {}'.format(
                xmlids
            )
        )

    xmlid = imd.read(xmlids, ['model', 'res_id'])[0]
    if xmlid['model'] != 'account.invoice.pending.state.process':
        raise RuntimeError(
            'L’XML ID del Bo Social apunta al model inesperat: {}'.format(
                xmlid['model']
            )
        )
    return xmlid['res_id']


def write_csv(filename, policies, vat_by_partner_id, partner_name_by_id):
    if sys.version_info[0] < 3:
        output = open(filename, 'wb')
    else:
        output = open(filename, 'w', newline='', encoding='utf-8')

    try:
        writer = csv.writer(output)
        writer.writerow([
            'polissa_id', 'contracte', 'estat', 'data_alta', 'cnae',
            'titular', 'cif_titular',
        ])
        for policy in sorted(policies, key=lambda item: item['id']):
            titular_id = many2one_id(policy.get('titular'))
            cnae = policy.get('cnae')
            row = [
                policy['id'], policy.get('name') or '',
                policy.get('state') or '', policy.get('data_alta') or '',
                cnae[1] if cnae else '',
                partner_name_by_id.get(titular_id, ''),
                vat_by_partner_id.get(titular_id, ''),
            ]
            if sys.version_info[0] < 3:
                row = [
                    value.encode('utf-8') if isinstance(value, text_type)
                    else value for value in row
                ]
            writer.writerow(row)
    finally:
        output.close()


def count_enterprise_bosocial_policies(output_filename):
    erp = Client(**dbconfig.erppeek)
    process_id = get_bono_social_process_id(erp)

    polissa_model = erp.model('giscedata.polissa')
    polissa_ids = polissa_model.search([('process_id', '=', process_id)])
    policies = polissa_model.read(
        polissa_ids, ['name', 'state', 'data_alta', 'cnae', 'titular']
    ) if polissa_ids else []

    titular_ids = sorted(set(
        many2one_id(policy['titular'])
        for policy in policies
        if policy.get('titular')
    ))
    partner_model = erp.model('res.partner')
    partners = partner_model.read(
        titular_ids, ['name', 'vat']
    ) if titular_ids else []
    vat_by_partner_id = dict(
        (partner['id'], partner.get('vat')) for partner in partners
    )
    partner_name_by_id = dict(
        (partner['id'], partner.get('name')) for partner in partners
    )

    matches = []
    for policy in policies:
        titular_id = many2one_id(policy.get('titular'))
        if titular_id and is_enterprise_vat(vat_by_partner_id.get(titular_id)):
            matches.append(policy)

    write_csv(output_filename, matches, vat_by_partner_id, partner_name_by_id)

    print('CSV generat: {}'.format(output_filename))
    print('Pòlisses amb procés Bo Social: {}'.format(len(policies)))
    print(
        'D’aquestes, amb CIF d’empresa vàlid al titular: {}'.format(
            len(matches)
        )
    )

    if matches:
        print('Distribució per estat:')
        counts_by_state = Counter(policy.get('state') or '(sense estat)'
                                  for policy in matches)
        for state, count in sorted(counts_by_state.items()):
            print('  {}: {}'.format(state, count))

        print('Contractes afectats (id, nom, estat, data alta, CNAE):')
        for policy in sorted(matches, key=lambda item: item['id']):
            cnae = policy.get('cnae')
            cnae_label = cnae[1] if cnae else ''
            print('  {}, {}, {}, {}, {}'.format(
                policy['id'], policy.get('name') or '',
                policy.get('state') or '', policy.get('data_alta') or '',
                cnae_label,
            ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=(
            'Exporta a CSV pòlisses en procés Bo Social amb CIF d’empresa '
            'vàlid al titular.'
        )
    )
    parser.add_argument(
        '--output', default='polisses_bosocial_cif_empresa.csv',
        help='Fitxer CSV de sortida (per defecte: %(default)s)',
    )
    args = parser.parse_args()
    count_enterprise_bosocial_policies(args.output)
