# -*- coding: utf-8 -*-
from __future__ import absolute_import
import dbconfig
from erppeek import Client
from consolemsg import success
from tqdm import tqdm

O = Client(**dbconfig.erppeek)  # noqa: E741

write_vals = False

# Hardcoded IDs handle with extremely caution, do not use in production without validation.
fp_change_map = [
    (98, 88),
    (97, 87),
    (39, 90),
    (99, 89),
    (96, 82),
    (102, 86),
    (103, 85),
]

pol_obj = O.GiscedataPolissa
mod_obj = O.GiscedataPolissaModcontractual

for fp_old, fp_new in tqdm(fp_change_map):
    pol_ids = pol_obj.search([
        ('fiscal_position_id', '=', fp_old),
        ('state', 'in', ['activa', 'esborrany', 'baixa'])
    ])

    """ slow version
    for p_id in tqdm(pol_ids):
        pol = pol_obj.browse(p_id)
        if write_vals:
            pol.fiscal_position_id = fp_new
            pol.modcontractual_activa.fiscal_position_id = fp_new
    """

    pol_data = pol_obj.read(pol_ids, ['modcontractual_activa'])
    mod_ids = [p['modcontractual_activa'][0] for p in pol_data if p['modcontractual_activa']]

    if write_vals:
        pol_obj.write(pol_ids, {'fiscal_position_id': fp_new})
        mod_obj.write(mod_ids, {'fiscal_position_id': fp_new})

    success("FP {} -> {}: {} polisses actualitzades {} modcons actualitzades {}".format(
            fp_old, fp_new, len(pol_ids), len(mod_ids), "Si" if write_vals else "No"))
