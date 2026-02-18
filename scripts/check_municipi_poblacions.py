# -*- coding: utf-8 -*-
import argparse
import requests
import csv
from collections import defaultdict
import psycopg2
from consolemsg import success, step, warn
import dbconfig

CSV_URL = (
    "https://raw.githubusercontent.com/inigoflores/"
    "ds-codigos-postales-ine-es/refs/heads/master/data/codigos_postales_municipios.csv"
)


def get_db_cursor():
    try:
        dbconn = psycopg2.connect(**dbconfig.psycopg)
    except Exception, ex:
        warn("Unable to connect to database {}", str(dbconfig.psycopg))
        raise ex

    return dbconn.cursor()


def get_db_data(dbcur):
    sql_query = """
        select
        addr.id as addr_id,
        addr.zip as zip,
        mun_addr.ine as mun_addr_ine,
        mun_pob.ine as mun_pob_ine,
        mun_addr.name as mun_addr_name,
        mun_pob.name as mun_pob_name,
        addr.street as street,
        addr.id_poblacio
        from res_partner_address addr
        inner join res_poblacio pob on addr.id_poblacio = pob.id
        inner join res_municipi mun_addr on addr.id_municipi = mun_addr.id
        inner join res_municipi mun_pob on pob.municipi_id = mun_pob.id
        where pob.municipi_id != addr.id_municipi;
    """
    try:
        dbcur.execute(sql_query)
    except Exception, ex:
        warn('Failed executing query')
        warn(sql_query)
        raise ex

    db_data = [
        {
            'addr_id': record[0],
            'zip': record[1],
            'mun_addr_ine': record[2],
            'mun_pob_ine': record[3],
            'mun_addr_name': record[4],
            'mun_pob_name': record[5],
            'street': record[6],
            'id_pobacio': record[7]
        } for record in dbcur.fetchall()
    ]
    step("{} adreçes amb municipi i poblacions diferents trobades a la BBDD", len(db_data))
    return db_data


def get_cp_ines_dict():
    cp_to_ines = defaultdict(set)

    with requests.get(CSV_URL, stream=True) as r:
        r.raise_for_status()
        lines = (line for line in r.iter_lines())
        reader = csv.reader(lines)

        for row in reader:
            cp, ine = row[0].strip(), row[1].strip()
            cp_to_ines[cp].add(ine)

    # There is a zipcode.py with this structure, if in the future we want to use it:
    # for cp, lines in ZIPCODES.items():
    #     for vals in lines:
    #         cp_to_ines[cp].add(vals['ine'])

    step("{} CP del CSV carregats", len(cp_to_ines))
    return cp_to_ines


def get_cp_ine_from_csv(cp_to_ines, cp, candidats):
    real_ines = cp_to_ines.get(cp, set())
    coincidencies = real_ines.intersection(candidats)
    return coincidencies


def main(output_path):
    cp_to_ines = get_cp_ines_dict()
    cur = get_db_cursor()
    db_data = get_db_data(cur)
    municipi_ok_addr_ids = []
    out_csv_data = []
    for data in db_data:
        candidats = {data['mun_addr_ine'], data['mun_pob_ine']}
        res_ine = get_cp_ine_from_csv(cp_to_ines, data['zip'], candidats)
        if data['mun_addr_ine'] in res_ine:
            municipi_ok_addr_ids.append(data['addr_id'])
            data['type'] = 'municipi OK'
        elif data['mun_pob_ine'] in res_ine:
            warn(
                "({}) CP {} coincideix amb poblacio {} en comptes de municipi {}, mirar carrer: {}",
                data['addr_id'], data['zip'],
                data['mun_pob_name'].decode('utf-8'), data['mun_addr_name'].decode('utf-8'),
                data['street'].decode('utf-8'),
            )
            data['type'] = 'CP coincideix amb poblacio'
        else:
            warn(
                "({}) CP {} no coincideix ni amb municipi {} ni amb poblacio {}, mirar carrer: {}",
                data['addr_id'], data['zip'],
                data['mun_addr_name'].decode('utf-8'), data['mun_pob_name'].decode('utf-8'),
                data['street'].decode('utf-8'),
            )
            data['type'] = 'CP no coincideix amb res'
        out_csv_data.append(data)

    success(str(len(municipi_ok_addr_ids))
            + " adreces amb l'adreça del municipi correcte. Per arreglar-les, executar:")
    formatted_ids = ', '.join((str(id_) for id_ in municipi_ok_addr_ids))
    print("update res_partner_address set id_poblacio = null where id in (" + formatted_ids + ");")

    if output_path:
        fieldnames = sorted(out_csv_data[0].keys())
        with open(output_path, "wb") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in out_csv_data:
                clean_row = {}
                for k, v in row.items():
                    if isinstance(v, unicode):
                        clean_row[k] = v.encode("utf-8")
                    else:
                        clean_row[k] = v
                writer.writerow(clean_row)
        success("CSV escrit correctament")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check address with different municipi - poblacions")
    parser.add_argument(
        "--output_path",
        dest="output_path",
        type=str,
        default=None,
        help="Path for a detailed CSV output",
    )
    args = parser.parse_args()
    main(args.output_path)
