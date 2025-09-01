# -*- coding: utf-8 -*-
# Script per actualitzar els nous camps del mòdul som_sortida
from __future__ import print_function
from tqdm import tqdm
import json
from erppeek import Client
from collections import defaultdict
from datetime import date, datetime, timedelta
import configdb


# Queries to execute previous to running this script and go from clean and faster:
#
# TRUNCATE TABLE public.som_sortida_history CONTINUE IDENTITY RESTRICT;
#
# update giscedata_polissa
# set sortida_state_id = null, en_process_de_sortida = null, te_socia_real_vinculada = null
# ;
#
# update giscedata_polissa
# set sortida_state_id = 1, en_process_de_sortida = false, te_socia_real_vinculada = true
# where soci != 222444;


c = Client(**configdb.erppeek)


state_correcte_id = c.model('ir.model.data').get_object_reference(
    'som_sortida', 'enviar_cor_correcte_pending_state')[1]
state_sense_socia_id = c.model('ir.model.data').get_object_reference(
    'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state')[1]
state_30d_id = c.model('ir.model.data').get_object_reference(
    'som_sortida', 'enviar_cor_falta_un_mes_pending_state')[1]
state_15d_id = c.model('ir.model.data').get_object_reference(
    'som_sortida', 'enviar_cor_falta_15_dies_pending_state')[1]
state_7d_id = c.model('ir.model.data').get_object_reference(
    'som_sortida', 'enviar_cor_falta_7_dies_pending_state')[1]


nifs_ct_ss = []
polisses_segons_estat = defaultdict(list)


def es_socia_ct_ss(socia_nif):
    """
    Check if the polissa is linked to a CT SS socia.
    :param socia_nif: NIF of the socia
    :return: True if the socia is in the ct ss campaing, False otherwise
    """
    global nifs_ct_ss
    if not nifs_ct_ss:
        config_obj = c.model('res.config')
        config_id = config_obj.search([('name', '=', 'llista_nifs_socia_ct_ss')])
        nifs_ct_ss = config_obj.browse(config_id).value[0]
        nifs_ct_ss = json.loads(nifs_ct_ss)
    return socia_nif in nifs_ct_ss


def assignar_estat_i_historic(pol_id, estat_id, change_date=None):
    """
    Assigna l'estat de sortida a la pòlissa i crea l'entrada a l'històric
    :param pol_id: ID de la pòlissa
    :param estat_id: ID de l'estat a assignar
    :param data_inici: Data d'inici del estat
    """
    c.model('giscedata.polissa').write(pol_id, {'sortida_state_id': estat_id})
    c.model('som.sortida.history').create({
        'polissa_id': pol_id,
        'pending_state_id': estat_id,
        'change_date': (change_date or datetime.now().date()).strftime('%Y-%m-%d')
    })


polisses_penents = c.model('giscedata.polissa').search([
    ('state', 'in', ['activa', 'esborrany']),
    ('sortida_state_id', '=', None),
])

for pol_id in tqdm(polisses_penents, desc="Actualitzant polisses"):
    pol = c.model('giscedata.polissa').browse(pol_id)
    if pol.soci and pol.soci_nif and es_socia_ct_ss(pol.soci_nif):
        data_inici = pol.modcontractual_activa and pol.modcontractual_activa.data_inici
        data_inici = data_inici or pol.data_alta or datetime.now().date()
        data_inici = (
            data_inici if isinstance(data_inici, date)
            else datetime.strptime(data_inici, '%Y-%m-%d').date()
        )
        if not pol.sortida_state_id:
            if not c.model('som.sortida.history').search([('polissa_id', '=', pol_id)]):
                # Si no hi ha historial, crear-lo
                c.model('som.sortida.history').create({
                    'polissa_id': pol_id,
                    'pending_state_id': state_sense_socia_id,
                    'change_date': data_inici.strftime('%Y-%m-%d')
                })
        dies_restants = (data_inici + timedelta(days=365) - datetime.now().date()).days
        if dies_restants < 7:
            assignar_estat_i_historic(pol_id, state_7d_id)
            polisses_segons_estat['7 dies'].append(pol_id)
        elif dies_restants < 15:
            assignar_estat_i_historic(pol_id, state_15d_id)
            polisses_segons_estat['15 dies'].append(pol_id)
        elif dies_restants < 30:
            assignar_estat_i_historic(pol_id, state_30d_id)
            polisses_segons_estat['30 dies'].append(pol_id)
        else:
            assignar_estat_i_historic(pol_id, state_sense_socia_id, data_inici)
            polisses_segons_estat['sense socia'].append(pol_id)
    else:
        # Assignar l'estat de sortida correcte
        c.model('giscedata.polissa').write(pol_id, {'sortida_state_id': state_correcte_id})
        polisses_segons_estat['correcte'].append(pol_id)

        if c.model('som.sortida.history').search([('polissa_id', '=', pol_id)]):
            # Si ja hi ha historial, borrar-lo
            c.model('som.sortida.history').unlink(
                c.model('som.sortida.history').search([('polissa_id', '=', pol_id)]),
            )

for estat, polisses in polisses_segons_estat.items():
    print("Polisses amb estat '{}': {}".format(estat, len(polisses)))
print("Actualització completa.")
