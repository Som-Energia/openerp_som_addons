# -*- coding: utf-8 -*-
# Script per actualitzar els nous camps del mòdul som_sortida
from __future__ import print_function
from tqdm import tqdm
import json
from erppeek import Client
import configdb

c = Client(**configdb.erppeek)

pol_sense_state = c.model('giscedata.polissa').search([('sortida_state_id', '=', False)])

state_sense_socia_id = c.model('ir.model.data').get_object_reference(
    'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state')[1]
pol_sense_state = c.model('giscedata.polissa').search(
    [('sortida_state_id', '=', state_sense_socia_id)])


polisses_correctes = []
polisses_no_soci = []


def es_socia_promocional(socia_nif):
    """
    Check if the polissa is linked to a promotional socia.
    :param socia_nif: NIF of the socia
    :return: True if the socia is promotional, False otherwise
    """
    config_obj = c.model('res.config')
    config_id = config_obj.search([('name', '=', 'llista_nifs_socia_promocional')])
    nifs_promocionals = config_obj.browse(config_id).value[0]
    nifs_promocionals = json.loads(nifs_promocionals)
    return socia_nif in nifs_promocionals


for pol_id in tqdm(pol_sense_state, desc="Actualitzant pòlisses"):
    pol = c.model('giscedata.polissa').browse(pol_id)
    if pol.soci and pol.soci_nif and es_socia_promocional(pol.soci_nif) and True:
        # Assignar l'estat de sortida sense sòcia
        state_sense_socia_id = c.model('ir.model.data').get_object_reference(
            'som_sortida', 'enviar_cor_contrate_sense_socia_pending_state')[1]
        c.model('giscedata.polissa').write(pol_id, {'sortida_state_id': state_sense_socia_id})
        polisses_no_soci.append(pol_id)

        if not c.model('som.sortida.history').search([('polissa_id', '=', pol_id)]):
            # Si no hi ha historial, crear-lo
            c.model('som.sortida.history').create({
                'polissa_id': pol_id,
                'pending_state_id': state_sense_socia_id,
                'change_date': pol.data_alta
            })
    else:
        # Assignar l'estat de sortida correcte
        state_correcte_id = c.model('ir.model.data').get_object_reference(
            'som_sortida', 'enviar_cor_correcte_pending_state')[1]
        c.model('giscedata.polissa').write(pol_id, {'sortida_state_id': state_correcte_id})
        polisses_correctes.append(pol_id)

        if c.model('som.sortida.history').search([('polissa_id', '=', pol_id)]):
            # Si ja hi ha historial, actualitzar-lo
            c.model('som.sortida.history').unlink(
                c.model('som.sortida.history').search([('polissa_id', '=', pol_id)]),
            )

print("Polisses amb estat correcte actualitzades: {}".format(len(polisses_correctes)))
print("Polisses sense sòcia actualitzades: {}".format(len(polisses_no_soci)))
print("Actualització completa.")
