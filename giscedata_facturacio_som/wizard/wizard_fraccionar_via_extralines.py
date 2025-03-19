# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from datetime import timedelta, datetime
from osv.osv import TransactionExecute


class WizardFraccionarViaExtralines(osv.osv_memory):

    _name = "wizard.fraccionar.via.extralines"
    _inherit = "wizard.fraccionar.via.extralines"

    def action_fraccionar_via_extralines(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, ids)[0]

        if not wiz.first_term_payment:
            return super(WizardFraccionarViaExtralines, self).action_fraccionar_via_extralines(
                cursor, uid, ids, context
            )

        factura_ids = context.get("active_ids")
        factura_o = self.pool.get("giscedata.facturacio.factura")
        user_o = self.pool.get("res.users")
        data_final = (
            datetime.strptime(wiz.data_inici, "%Y-%m-%d") + timedelta(days=365 * 10)
        ).strftime("%Y-%m-%d")

        msgs = []
        has_errors = False
        for info in factura_o.read(cursor, uid, factura_ids, ["number"]):
            base_res = _(u"Resultat '{0}' (ID {1}):\n").format(info["number"], info["id"])
            try:
                factura_teo = TransactionExecute(cursor.dbname, uid, "giscedata.facturacio.factura")
                factura = factura_o.browse(cursor, uid, info["id"])
                ntermes = wiz.ntermes - 1
                amount = (factura.residual / wiz.ntermes) * ntermes
                factura_teo.fraccionar_via_extralines(
                    info["id"],
                    ntermes,
                    wiz.data_inici,
                    data_final,
                    journal_id=wiz.journal_id.id,
                    amount=amount,
                    context=context,
                )
                comment_head = "{} ({}): Fraccionament extralines en {} quotes.\n".format(
                    datetime.now().strftime("%Y-%m-%d"),
                    "".join(
                        [
                            word[0]
                            for word in user_o.read(cursor, uid, uid, ["name"])["name"].split(" ")
                        ]
                    ),
                    wiz.ntermes,
                )
                old_comment = factura.comment or ""
                new_comment = comment_head + old_comment
                factura_teo.write(info["id"], {"comment": new_comment})

            except Exception as e:
                has_errors = True
                if hasattr(e, "value"):
                    res = e.value
                else:
                    res = str(e)
                msgs.append(base_res + res)

        if has_errors:
            msgs = [
                _(u"Hi ha hagut problemes al processar {0} factures: ").format(len(msgs))
            ] + msgs
            msg = "\n\n".join(msgs)
        else:
            msg = _(u"S'han processat totes les factures correctament.")

        msg = _(u"Número de factures processades: {0}.\n\n").format(len(factura_ids)) + msg

        final_state = "end" if not has_errors else "error"
        wiz.write({"info": msg, "state": final_state})
        return True

    _columns = {
        "first_term_payment": fields.boolean(
            "Carregar primer termini a la factura actual", required=True
        ),
    }

    _defaults = {
        "first_term_payment": lambda *a: True,
        "data_inici": lambda *a: (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
    }


WizardFraccionarViaExtralines()
