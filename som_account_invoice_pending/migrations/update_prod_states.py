# -*- coding: utf-8 -*-
"""Actualitza els pending states, partint del nostre fitxer d'estats
   també insereix una nova linia a IrModelData per als estats creats
   a mà"""

import sys
import logging
import configdb
import erppeek

from yamlns import namespace as ns
from consolemsg import step, warn
from io import open


def migrate():
    def find_my_ref(con, module, semid):
        IrModelData = con.model("ir.model.data")
        try:
            return IrModelData.get_object_reference(module, semid)[1]
        except Exception:
            return None

    msg = "You are requesting to: {}, do you want to continue? (Y/n)"
    step(msg.format(configdb.erppeek["server"]))
    answer = raw_input()
    while answer.lower() not in ["y", "n", ""]:
        answer = raw_input()
        step("Do you want to continue? (Y/n)")

    if answer in ["n", "N"]:
        sys.exit()

    c = erppeek.Client(**configdb.erppeek)
    logger = logging.getLogger("openerp.migration")

    logger.info(
        """
        Updating account.invoice.pending.state items that were created
        manually. This will add a pending_days_type value (On those
        null assigned).
    """
    )
    IrModelData = c.model("ir.model.data")
    PendingState = c.model("account.invoice.pending.state")

    states_in_db = [
        ns(
            PendingState.read(
                id, ["id", "name", "pending_days", "pending_days_type", "process_id", "weight"]
            )
        )
        for id in PendingState.search()
    ]

    msg = "A la DB he trobat els pending states amb id's: {}"
    step(msg.format(str([x.id for x in states_in_db])))

    with open("states.tsv", encoding="utf8") as tsv:
        lines = tsv.readlines()
        header = lines[0].split("\t")
        content = lines[1:]
        states_in_file = [
            ns((k.strip(), v.strip()) for k, v in zip(header, line.split("\t")))
            for line in sorted(content)
        ]

    full_states = {}
    for state in states_in_file:
        full_states[int(state.db_id)] = {
            "new_id": state.db_id,
            "new_name": state.name,
            "new_weight": state.weight,
            "new_semid": state.id,
            "new_module": state.module,
            "new_pending_days_type": state.pending_days_type,
            "new_pending_days": state.pending_days,
        }
    warn("surto del primer for")
    for state in states_in_db:
        full_states[int(state.id)]["db_id"] = state.id
        full_states[int(state.id)]["db_name"] = state.name
        full_states[int(state.id)]["db_weight"] = state.weight
        full_states[int(state.id)]["db_pendingd"] = state.pending_days
        full_states[int(state.id)]["db_pendingdtype"] = state.pending_days_type
        module = full_states[int(state.id)]["new_module"]
        semid = full_states[int(state.id)]["new_semid"]
        full_states[int(state.id)]["db_semid"] = (
            None if find_my_ref(c, module, semid) is None else semid
        )
        full_states[int(state.id)]["db_module"] = (
            None if full_states[int(state.id)]["db_semid"] is None else module
        )

    for state in full_states:
        print(
            """\n
(DB)id: {db_id}\t\t\t\t\t->\t{new_id},
(DB)nom: {db_nom},\t\t->\t{new_nom},
(DB)pes: {db_pes},\t\t\t\t\t->\t{new_pes},
(DB)pending_days_type: {db_pendingd},\t\t\t->\t{new_pendingd},
(DB)pending_days: {db_pendingdtype},\t\t\t->\t{new_pendingdtype},
(DB)semid: {db_semid},\t\t\t\t->\t{new_semid},
(DB)module: {db_module}\t\t->\t{new_module}""".format(
                db_id=full_states[state]["db_id"],
                db_nom=full_states[state]["db_name"],
                db_pes=full_states[state]["db_weight"],
                db_pendingd=full_states[state]["db_pendingd"],
                db_pendingdtype=full_states[state]["db_pendingdtype"],
                db_semid=full_states[state]["db_semid"],
                db_module=full_states[state]["db_module"],
                new_id=full_states[state]["new_id"],
                new_nom=full_states[state]["new_name"],
                new_pes=full_states[state]["new_weight"],
                new_pendingd=full_states[state]["new_pending_days"],
                new_pendingdtype=full_states[state]["new_pending_days_type"],
                new_semid=full_states[state]["new_semid"],
                new_module=full_states[state]["new_module"],
            )
        )

    for state in full_states.items():
        if state[1]["db_module"] is None:
            warn(str(state[1]["db_id"]) + " : " + str(state[1]["db_name"]) + "s'actualitzara.")

    msg = "Do you want to update? (y/n)"
    step(msg.format(configdb.erppeek["server"]))
    answer = raw_input()
    while answer.lower() not in ["y", "n", ""]:
        answer = raw_input()
        step("Do you want to update? (y/n)")

    if answer in ["n", "N"]:
        sys.exit()

    for state in full_states.items():
        if state[1]["db_module"] is None:
            IrModelData.create(
                {
                    "noupdate": True,
                    "name": state[1]["new_semid"],
                    "module": state[1]["new_module"],
                    "model": "account.invoice.pending.state",
                    "res_id": state[1]["db_id"],
                }
            )


if __name__ == "__main__":
    migrate()
