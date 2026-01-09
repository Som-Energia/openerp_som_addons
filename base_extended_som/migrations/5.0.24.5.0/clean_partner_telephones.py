# -*- encoding: utf-8 -*-
from __future__ import print_function
import configdb
from erppeek import Client
import csv
from tqdm import tqdm

# Connect to ERP
c = Client(**configdb.erppeek)

doit = False
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
            return None

    if len(phone_number) == 9:
        # print("new phone {}".format(phone_number))
        phones_changed.append(phone_number)
        return phone_number
    else:
        # print("Phone number {0} of partner address {1} is not valid".format(phone_number, partner_address_id))  # noqa:E501
        phones_not_valid.append(phone_number)
        return None


partner_address_list = c.ResPartnerAddress.search([])

rows = []
for partner_address_id in tqdm(partner_address_list, desc="Processing partner addresses"):
    partner_address = c.ResPartnerAddress.browse(partner_address_id)
    row = {'partner_address_id': partner_address_id}
    old_phone = partner_address.phone
    if old_phone and len(old_phone) != 9:
        phones_to_change.append(old_phone)
        # print("Partner address {0} has an invalid phone number: {1}".format(partner_address_id, old_phone))  # noqa:E501
        new_phone = clean_partner_telephones(partner_address_id, old_phone)
        row['old_phone'] = old_phone
        row['new_phone'] = new_phone
        if new_phone:
            # print("New phone number of {0}: {1}".format(partner_address_id, new_phone))
            if doit:
                c.ResPartnerAddress.write(partner_address_id, {
                    'notes': partner_address.notes + "\n2025/06/20: Procés de neteja de telèfons, el telèfon antic era: {}".format(partner_address.phone)})  # noqa:E501
                partner_address.phone = new_phone
                partner_address.save()
    old_mobile = partner_address.mobile
    if old_mobile and len(old_mobile) != 9:
        phones_to_change.append(old_mobile)
        # print("Partner address {0} has an invalid mobile number: {1}".format(partner_address_id, old_mobile))  # noqa:E501
        new_mobile = clean_partner_telephones(partner_address_id, old_mobile)
        row['old_mobile'] = old_mobile
        row['new_mobile'] = new_mobile
        if new_mobile:
            # print("New mobile number of {0}: {1}".format(partner_address_id, new_mobile))
            if doit:
                c.ResPartnerAddress.write(partner_address_id, {
                    'notes': partner_address.notes
                    + "\n2025/06/20: Procés de neteja de telèfons, el mòbil antic era: {}\n".format(partner_address.mobile)})  # noqa:E501
                partner_address.mobile = new_mobile
                partner_address.save()

    if len(row.keys()) > 1:
        rows.append(row)

print("Telèfons a canviar: {}".format(len(phones_to_change)))
print("Telèfons canviats: {}".format(len(phones_changed)))
print("Telèfons eliminats: {}".format(len(phones_not_valid)))


with open('canvis_telefon.csv', 'w') as csvfile:
    fieldnames = ['partner_address_id', 'old_phone', 'new_phone', 'old_mobile', 'new_mobile']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
