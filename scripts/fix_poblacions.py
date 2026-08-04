# -*- coding: utf-8 -*-

import psycopg2
from consolemsg import warn
from tqdm import tqdm
import configdb
from erppeek import Client

municipi_poblacio_cache = {}


def get_db_cursor():
    try:
        dbconn = psycopg2.connect(**configdb.psycopg)
    except Exception as ex:
        warn("Unable to connect to database {}", str(configdb.psycopg))
        raise ex

    return dbconn.cursor()


def execute_sql(dbcur, sql_query):
    try:
        dbcur.execute(sql_query)
    except Exception as ex:
        warn('Failed executing query')
        warn(sql_query)
        raise ex

    return [record[0] for record in dbcur.fetchall()]


def get_first_poblacio(c, municipi_id):
    if municipi_id in municipi_poblacio_cache:
        return municipi_poblacio_cache[municipi_id]

    poblacio_ids = c.model("res.poblacio").search([("municipi_id", "=", municipi_id)], limit=1)
    poblacio_id = poblacio_ids and poblacio_ids[0] or None
    municipi_poblacio_cache[municipi_id] = poblacio_id
    return poblacio_id


c = Client(**configdb.erppeek)
cur = get_db_cursor()

address_obj = c.model("res.partner.address")

sql = """
    select rpa.id
    from res_partner_address rpa
    inner join res_poblacio rp on rpa.id_poblacio = rp.id
    where id_poblacio is not NULL and rp.municipi_id != rpa.id_municipi;
"""
ids = execute_sql(cur, sql)

total = 0
pbar = tqdm(address_obj.browse(ids))
for address in pbar:
    total += 1
    note = u"Població arreglada, antiga " + address.id_poblacio.name
    pbar.set_description(note)
    nova_poblacio = get_first_poblacio(c, address.id_municipi.id)
    notes = address.notes or ''
    if notes:
        notes = notes + "\n" + note
    else:
        notes = note
    address_obj.write(address.id, {'id_poblacio': nova_poblacio, 'notes': notes})

print("Total arreglades: " + str(total))
