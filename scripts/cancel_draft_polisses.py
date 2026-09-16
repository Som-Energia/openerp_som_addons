# -*- coding: utf-8 -*-
"""Cancel draft policies created within an inclusive date range.

Usage:
    PYENV_VERSION=erp python scripts/cancel_draft_polisses.py \
        2025-01-01 2025-01-31

Add ``--apply`` to execute the changes. Without it, the script only lists
how many policies would be cancelled. The cancellation is performed through
the OpenERP workflow, rather than writing the state directly.
"""
from __future__ import absolute_import, print_function

import argparse
import sys
from datetime import datetime, timedelta

import configdb
from erppeek import Client


POLISSA_MODEL = "giscedata.polissa"
DRAFT_STATE = "esborrany"


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            "La data ha de tenir el format YYYY-MM-DD: {0}".format(value)
        )


def get_draft_polissa_ids(polissa_obj, start_date, end_date):
    """Return draft policies created from start_date through end_date."""
    end_date_exclusive = end_date + timedelta(days=1)
    domain = [
        ("state", "=", DRAFT_STATE),
        ("create_date", ">=", start_date.isoformat()),
        ("create_date", "<", end_date_exclusive.isoformat()),
    ]
    return polissa_obj.search(domain, order="id")


def confirm():
    builtins = __import__("__builtin__" if sys.version_info[0] == 2 else "builtins")
    input_function = getattr(builtins, "raw_input" if sys.version_info[0] == 2 else "input")
    answer = input_function("Vols continuar? [y/N] ")
    return answer.lower() in ("y", "yes", "s", "si", "sí")


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Cancel·la pòlisses en esborrany creades entre dues dates."
    )
    parser.add_argument("start_date", type=parse_date, help="Data inicial (YYYY-MM-DD)")
    parser.add_argument("end_date", type=parse_date, help="Data final inclusiva (YYYY-MM-DD)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Executa les cancel·lacions; sense aquesta opció només fa una previsualització.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="No demana confirmació (requereix --apply).",
    )
    options = parser.parse_args(args)
    if options.end_date < options.start_date:
        parser.error("La data final ha de ser igual o posterior a la data inicial.")
    if options.yes and not options.apply:
        parser.error("L'opció --yes requereix --apply.")
    return options


def main(args=None):
    options = parse_args(args)
    client = Client(**configdb.erppeek)
    polissa_obj = client.model(POLISSA_MODEL)
    polissa_ids = get_draft_polissa_ids(
        polissa_obj, options.start_date, options.end_date
    )

    print(
        "S'han trobat {0} pòlisses en esborrany creades entre {1} i {2}.".format(
            len(polissa_ids), options.start_date.isoformat(), options.end_date.isoformat()
        )
    )
    if polissa_ids:
        print("IDs: {0}".format(", ".join(map(str, polissa_ids))))

    if not options.apply:
        print("Previsualització: no s'ha modificat cap pòlissa. Usa --apply per executar-ho.")
        return 0

    if not options.yes and not confirm():
        print("Operació cancel·lada per l'usuari.")
        return 0

    failed_ids = []
    for polissa_id in polissa_ids:
        try:
            client.exec_workflow(POLISSA_MODEL, "cancelar", polissa_id)
        except Exception as error:
            failed_ids.append(polissa_id)
            print("No s'ha pogut cancel·lar la pòlissa {0}: {1}".format(polissa_id, error))

    cancelled_count = len(polissa_ids) - len(failed_ids)
    print("S'han cancel·lat {0}/{1} pòlisses.".format(cancelled_count, len(polissa_ids)))
    if failed_ids:
        print("IDs no cancel·lats: {0}".format(", ".join(map(str, failed_ids))))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
