# -*- encoding: utf-8 -*-
from __future__ import print_function
import configdb
from erppeek import Client
import csv
from tqdm import tqdm

# Connect to ERP
c = Client(**configdb.erppeek)

doit = True
phones_to_change = []
phones_changed = []
phones_not_valid = []


def clean_partner_telephones(partner_address_id, phone_number):
    # print("old phone {}".format(phone_number))
    if ',' in phone_number:
        phone_number = phone_number.split(',')[0]
    if '/' in phone_number:
        phone_number = phone_number.split('/')[0]
    phone_number = phone_number.replace(" ", "")
    phone_number = phone_number.replace("-", "")
    phone_number = phone_number.replace(".", "")
    phone_number = phone_number.replace("(", "")
    phone_number = phone_number.replace(")", "")
    phone_number = phone_number.replace("+34", "")

    while phone_number.startswith("0"):
        phone_number = phone_number[1:]
    if phone_number.startswith("34"):
        phone_number = phone_number[2:]

    # Search for a non-numeric character found in phone number
    for char in phone_number:
        if not char.isdigit():
            phones_not_valid.append(phone_number)
            return ''

    if len(phone_number) == 9:
        # print("new phone {}".format(phone_number))
        phones_changed.append(phone_number)
        return phone_number
    else:
        # print("Phone number {0} of partner address {1} is not valid".format(phone_number, partner_address_id))  # noqa:E501
        phones_not_valid.append(phone_number)
        return ''


partner_address_list = c.ResPartnerAddress.search([])[224000:]
partner_address_list = [283313]

rows = []
for partner_address_id in tqdm(partner_address_list, desc="Processing partner addresses"):  # noqa:C901,E501
    partner_address = c.ResPartnerAddress.browse(partner_address_id)
    row = {'partner_address_id': partner_address_id}
    old_phone = partner_address.phone
    if old_phone and len(old_phone) != 9:
        phones_to_change.append(old_phone)
        # print("Partner address {0} has an invalid phone number: {1}".format(partner_address_id, old_phone))  # noqa:E501
        new_phone = clean_partner_telephones(partner_address_id, old_phone)
        row['old_phone'] = old_phone
        row['new_phone'] = new_phone
        if old_phone != new_phone:
            # print("New phone number of {0}: {1}".format(partner_address_id, new_phone))
            if doit:
                previous_notes = partner_address.notes if partner_address.notes  else ''
                c.ResPartnerAddress.write(partner_address_id, {
                    'notes': previous_notes + "\n2025/06/20: Procés de neteja de telèfons, el telèfon antic era: {}".format(old_phone),  # noqa:E501
                    'phone': new_phone,
                })
                partner_address = c.ResPartnerAddress.browse(partner_address_id)
    old_mobile = partner_address.mobile
    if old_mobile and len(old_mobile) != 9:
        phones_to_change.append(old_mobile)
        # print("Partner address {0} has an invalid mobile number: {1}".format(partner_address_id, old_mobile))  # noqa:E501
        new_mobile = clean_partner_telephones(partner_address_id, old_mobile)
        row['old_mobile'] = old_mobile
        row['new_mobile'] = new_mobile
        if old_mobile != new_mobile:
            # print("New mobile number of {0}: {1}".format(partner_address_id, new_mobile))
            if doit:
                previous_notes = partner_address.notes if partner_address.notes else ''
                c.ResPartnerAddress.write(partner_address_id, {
                    'notes': previous_notes + "\n2025/06/20: Procés de neteja de telèfons, el mòbil antic era: {}\n".format(partner_address.mobile),  # noqa:E501
                    'mobile': new_mobile,
                })

    if len(row.keys()) > 1:
        rows.append(row)

    # Check if we phone and mobile are on their propper field
    partner_address = c.ResPartnerAddress.browse(partner_address_id)
    mobile_misplaced = False
    landline_misplaced = False
    if partner_address.phone:
        if c.ResPartnerAddress.check_mobile_or_landline_peek(partner_address.phone) == 'landline':
            pass
        else:
            mobile_misplaced = partner_address.phone
    if partner_address.mobile:
        if c.ResPartnerAddress.check_mobile_or_landline_peek(partner_address.mobile) == 'mobile':
            pass
        else:
            landline_misplaced = partner_address.mobile
    if mobile_misplaced or landline_misplaced:
        print("Telefons mobil {} o fixe {} mal posat:".format(mobile_misplaced, landline_misplaced))
    if doit:
        if mobile_misplaced:
            if not partner_address.mobile:
                c.ResPartnerAddress.write(partner_address_id, {
                    'mobile': mobile_misplaced,
                    'phone': '',
                })
            elif partner_address.mobile == mobile_misplaced:
                c.ResPartnerAddress.write(partner_address_id, {
                    'phone': '',
                })
            else:
                previous_notes = partner_address.notes if partner_address.notes else ''
                c.ResPartnerAddress.write(partner_address_id, {
                    'notes': previous_notes + "\n2025/06/20: Procés de neteja de telèfons, hi havia dos mòbils, l'atre era: {}\n".format(mobile_misplaced),  # noqa:E501
                })

        if landline_misplaced:
            if not partner_address.phone:
                c.ResPartnerAddress.write(partner_address_id, {
                    'phone': landline_misplaced,
                    'mobile': '',
                })
            elif partner_address.phone == landline_misplaced:
                c.ResPartnerAddress.write(partner_address_id, {
                    'mobile': '',
                })
            else:
                previous_notes = partner_address.notes if partner_address.notes else ''
                c.ResPartnerAddress.write(partner_address_id, {
                    'notes': previous_notes + "\n2025/06/20: Procés de neteja de telèfons, hi havia dos fixes, l'atre era: {}\n".format(landline_misplaced),  # noqa:E501
                })

print("Telèfons a canviar: {}".format(len(phones_to_change)))
print("Telèfons canviats: {}".format(len(phones_changed)))
print("Telèfons eliminats: {}".format(len(phones_not_valid)))


with open('canvis_telefon.csv', 'w') as csvfile:
    fieldnames = ['partner_address_id', 'old_phone', 'new_phone', 'old_mobile', 'new_mobile']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
