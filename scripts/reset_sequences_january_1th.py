# -*- coding: utf-8 -*-
from datetime import datetime
import dbconfig
from consolemsg import step, fail, success
from erppeek import Client

sequences_to_update = [
    "account.invoice.energia",
    "account.invoice.energia.ab",
    "account.invoice.energia.re",
    "payment.order",
    "rec.payment.order",
    "account.invoice.in_invoice",
    "account.invoice.out_invoice",
    "account.invoice.in_refund",
    "account.invoice.out_refund",
]


def reset_sequences():
    if datetime.today().day != 1 and datetime.today().month != 1:
        step(u"Només es permet reinicialitzar seqüències a l'1 de gener.")
        fail(u"Not today. Arya Stark")

    c = Client(**dbconfig.erppeek)
    step(u"Hem reiniciat les següents seqüències:")
    for seq_code in sequences_to_update:
        seq_id = c.IrSequence.search([("code", "=", seq_code)])[0]
        c.IrSequence.write(seq_id, {"number_next": 1})
        step(u"Seqüència %s resetejada a 1" % c.IrSequence.read(seq_id, ["name"])["name"])

    success(u"Feina feta. Apa, fins l'any que ve")


if __name__ == "__main__":
    reset_sequences()
