from erppeek import Client
from tqdm import tqdm
import configdb
import csv

c = Client(**configdb.erppeek)

file_path = '/tmp/coordis.csv'

cups_obj = c.model('giscedata.cups.ps')

cups_list = []

with open(file_path, "r") as csvfile:
    reader = csv.reader(csvfile, delimiter=",")
    for row in tqdm(reader):
        cups_list.append(
            {
                "name": row[0],
                "lat": str(row[2].replace(',', '.')),
                "long": str(row[4].replace(',', '.'))
            }
        )

for cups in tqdm(cups_list[1:]):
    cups_id = cups_obj.search([('name', '=', cups['name'])])
    if cups_id:
        write_vals = {
            'coordenada_latitud': cups['lat'],
            'coordenada_longitud': cups['long'],
            'coordenada_procedencia': 'altres',
            'coordenada_score': 'Manual'
        }

        cups_obj.write(cups_id[0], write_vals)
