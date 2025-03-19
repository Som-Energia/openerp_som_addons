import configdb
from erppeek import Client

O = Client(**configdb.erppeek)  # noqa: E741

msgs = O.PoweremailMailbox.search([("folder", "=", "drafts")])

print "Mails in draft folder: {}".format(len(msgs))  # noqa: E999
status = len(msgs) >= 100
print "Status (test): {}".format(status)

for msg_idx in msgs:
    msg = O.PoweremailMailbox.browse(msg_idx)
    msg.send_this_mail()

msgs = O.PoweremailMailbox.search([("folder", "=", "error")])

print "Mails in error folder: {}".format(len(msgs))
status = len(msgs) >= 100
print "Status (test): {}".format(status)

for msg_idx in msgs:
    msg = O.PoweremailMailbox.browse(msg_idx)
    msg.send_this_mail()

msgs = O.PoweremailMailbox.search([("folder", "=", "outbox")])

print "Mails in outbox folder: {}".format(len(msgs))
status = len(msgs) >= 100
print "Status (test): {}".format(status)

for msg_idx in msgs:
    msg = O.PoweremailMailbox.browse(msg_idx)
    msg.send_this_mail()
