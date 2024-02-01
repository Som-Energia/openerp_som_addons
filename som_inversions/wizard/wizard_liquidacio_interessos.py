# -*- coding: utf-8 -*-
from __future__ import division
from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta
from calendar import isleap
import netsvc
import pooler


class WizardLiquidacioInteressos(osv.osv_memory):
    """Assistent per liquidar els interessos."""

    _name = "wizard.liquidacio.interessos"
    _columns = {
        "account": fields.many2one(
            "account.account",
            "Compte a liquidar",
            help="Assignar la compte a liquidar. Si és la compta general "
            "liquidarà tots els interessos de les comptes filles. Si "
            "només es vol liquidar els interessos d'un soci s'ha "
            "d'assignar la compte específica.",
        ),
        "account_prefix": fields.char(
            "Prefix comptes",
            size=5,
            help=u"Selecciona els comptes a liquidar a partir del codi. Agafa "
            u"tots els comptes que comencin pel prefix especificat. Només "
            u"quan no s'ha seleccionat un compte específic",
        ),
        "date_invoice": fields.date("Data factura"),
        "date_start": fields.date("Data inici", required=True),
        "date_end": fields.date("Data final", required=True),
        "journal": fields.many2one(
            "account.journal", "Dirari per crear les factures", required=True
        ),
        "interes": fields.float("Interés anual (en %)", required=True),
        "product": fields.many2one("product.product", "Producte", required=True),
        "err": fields.text(
            "Missatges d'error",
            readonly=True,
        ),
        "calc": fields.text(
            "Missatges de càlcul",
            readonly=True,
        ),
        "state": fields.char("Estat", 50),
        "force": fields.boolean(
            "Forçar", help="Forçar els que el balanç sigui 0 a calcular-lo igualment"
        ),
    }

    _defaults = {"state": lambda *a: "init", "force": lambda *a: 0}

    def create_invoice(self, cursor, uid, ids, partner_id, context=None):
        """Funció que crearà les factures per liquidar els interessos."""
        inv_obj = self.pool.get("account.invoice")
        pt_obj = self.pool.get("payment.type")
        pt_CSB = pt_obj.search(cursor, uid, [("code", "=", "TRANSFERENCIA_CSB")])[0]
        wiz = self.browse(cursor, uid, ids[0])
        partner = self.pool.get("res.partner").browse(cursor, uid, partner_id)
        vals = {}
        vals.update(
            inv_obj.onchange_partner_id(
                cursor,
                uid,
                [],
                "in_invoice",
                partner_id,
            ).get("value", {})
        )
        if not partner.property_account_liquidacio:
            partner.button_assign_acc_410()
            partner = partner.browse()[0]
        vals.update(
            {
                "partner_id": partner_id,
                "type": "in_invoice",
                "name": "%s%s%s" % (wiz.journal.code, wiz.date_end.split("-")[0], partner.ref),
                "journal_id": wiz.journal.id,
                "account_id": partner.property_account_liquidacio.id,
                "partner_bank": partner.bank_inversions.id,
                "payment_type": pt_CSB,
            }
        )
        if wiz.date_invoice:
            vals["date_invoice"] = wiz.date_invoice
        inv_id = inv_obj.create(cursor, uid, vals)
        return inv_id

    def create_invoice_line(self, cursor, uid, ids, vals, context=None):
        """Funció que ens crearà les línies de les factures."""
        wiz = self.browse(cursor, uid, ids[0])
        il_obj = self.pool.get("account.invoice.line")
        inv = self.pool.get("account.invoice").browse(cursor, uid, vals["invoice_id"])
        l_vals = {}
        l_vals.update(
            il_obj.product_id_change(
                cursor,
                uid,
                [],
                product=vals["product_id"],
                uom=wiz.product.uom_id.id,
                partner_id=inv.partner_id.id,
                type="in_invoice",
            ).get("value", {})
        )
        l_vals["invoice_line_tax_id"] = [(6, 0, l_vals.get("invoice_line_tax_id", []))]
        l_vals.update(vals)
        il_obj.create(cursor, uid, l_vals)

    def calc(self, cursor, uid, ids, context=None):  # noqa: C901
        if not context:
            context = {}

        logger = netsvc.Logger()

        inv_ids = []
        msg = {}
        pre_calc = context.get("pre_calc", True)
        account_obj = self.pool.get("account.account")
        aml_obj = self.pool.get("account.move.line")
        inv_obj = self.pool.get("account.invoice")
        wiz = self.browse(cursor, uid, ids[0], context)
        interes = wiz.interes / 100
        if wiz.account.id:
            # Si s'ha selecionat un compte:
            # Busquem totes les comptes que siguin filles de la que tenim
            # actualment
            search_params = [("parent_id", "child_of", [wiz.account.id])]
        else:
            # Si s'ha escollit un prefix:
            # Busquem els comptes que comencen (codi) pel prefix especificat
            search_params = [("code", "=like", wiz.account_prefix + "%")]
        acc_ids = account_obj.search(cursor, uid, search_params)
        if not acc_ids and wiz.account.id:
            acc_ids = [wiz.account.id]
        if not acc_ids:
            raise osv.except_osv(
                _(u"Error Compte"),
                _(u"No s'ha trobat cap compte per liquidar amb el prefix " u"{0}").format(
                    wiz.account_prefix
                ),
            )

        total_acc = len(acc_ids)
        logger.notifyChannel(
            "liquidacio APO",
            netsvc.LOG_INFO,
            _(
                u"Calculem liquidació aportacions de {0} comptes ({1},{2})." u" pre calc: {3}"
            ).format(total_acc, wiz.account.id, wiz.account_prefix, pre_calc and "Si" or "No"),
        )
        counter = 0
        # acc_ids = acc_ids[counter:]

        for account in account_obj.browse(cursor, uid, acc_ids):
            if account.code == "163000000000":
                print("GENERIC")

            new_cursor = pooler.get_db(cursor.dbname).cursor()
            counter += 1
            if account.balance >= 0 and not wiz.force:
                continue
            key = "%s %s" % (account.code, account.name)
            logger.notifyChannel(
                "liquidacio APO",
                netsvc.LOG_INFO,
                _(u"{0:05d}/{1:05d} Compte {2}.").format(counter, total_acc, key),
            )
            msg.setdefault(key, {"err": [], "calc": []})
            search_params = [
                ("account_id", "=", account.id),
                ("period_id.special", "=", False),
                ("move_id.date", "<=", wiz.date_end),
            ]

            #            ml_ids = aml_obj.search(new_cursor, uid, search_params,
            #                                    order='date asc')
            partners = set()
            inv_id = None
            for mls in (
                aml_obj.q(new_cursor, uid).read(["id"], order_by=("id.asc",)).where(search_params)
            ):
                partners.add(aml_obj.read(cursor, uid, mls["id"], ["partner_id"])["partner_id"][0])
            for partner in partners:
                ml_data = (
                    aml_obj.q(new_cursor, uid)
                    .read(["id"], order_by=("id.asc",))
                    .where(search_params + [("partner_id", "=", partner)])
                )
                ml_ids = [ml["id"] for ml in ml_data]
                acum = 0
                mls = [x for x in aml_obj.browse(new_cursor, uid, ml_ids)]
                if not any([x.credit - x.debit for x in mls]):
                    msg[key]["calc"] += ["  No hi ha inversions"]
                    continue
                invoice_name = "%s%s%s" % (
                    wiz.journal.code,
                    wiz.date_end.split("-")[0],
                    mls[0].partner_id.ref,
                )
                if inv_obj.search_count(new_cursor, uid, [("name", "=", invoice_name)]):
                    msg[key]["err"] += [("  Ja existeix la factura %s creada." % invoice_name)]
                if not pre_calc:
                    if not mls[0].partner_id:
                        raise osv.except_osv(
                            _("Error"),
                            _(u"El moviment %s de la compta %s no té empresa " u"assignada")
                            % (mls[0].name, mls[0].account_id.code),
                        )
                    inv_id = self.create_invoice(new_cursor, uid, [ids[0]], mls[0].partner_id.id)
                    inv_ids.append(inv_id)
                year_days = isleap(int(wiz.date_end.split("-")[0])) and 366 or 365
                for idx, ml in enumerate(mls):
                    if not ml.partner_id:
                        msg[key]["err"] += [
                            "  Moviment: %s No Ref. Empresa " "assignada." % ml.name
                        ]
                    start = max(wiz.date_start, ml.date)
                    if idx + 1 < len(mls):
                        end = min(mls[idx + 1].date, wiz.date_end)
                    else:
                        end = wiz.date_end
                    start = datetime.strptime(start, "%Y-%m-%d")
                    end = datetime.strptime(end, "%Y-%m-%d")
                    days = (end - start).days
                    # Si els dies son negatius, vol dir que és un moviment anterior
                    # i no cal tenir-lo en compte
                    if days < 0:
                        days = 0
                    if len(mls) == idx + 1:
                        # Sumem un dia sempre a l'última part del bucle
                        days += 1
                    else:
                        end -= timedelta(1)
                    acum += ml.credit - ml.debit
                    # Si dies és 0, no cal processar la línia
                    if acum and days:
                        res = days * (interes / year_days) * acum
                        msg[key]["calc"] += [
                            "  De %s a %s: %s * %s/%s * %s: %s, partner_id: %s"
                            % (start, end, days, interes, year_days, acum, res, partner)
                        ]
                        if acum < 0:
                            msg[key]["err"] += [
                                "  Quantitat negativa pel partner_id %s" % (partner)
                            ]
                        if not pre_calc:
                            vals = {
                                "invoice_id": inv_id,
                                "note": _(
                                    "De %s a %s: %s * %s/%s * %s: %s"
                                    % (
                                        start.strftime("%d/%m/%Y"),
                                        end.strftime("%d/%m/%Y"),
                                        days,
                                        interes,
                                        year_days,
                                        acum,
                                        res,
                                    )
                                ),
                                "name": _(
                                    "De %s a %s"
                                    % (start.strftime("%d/%m/%Y"), end.strftime("%d/%m/%Y"))
                                ),
                                "quantity": acum,
                                "price_unit": days * (interes / year_days),
                                "product_id": wiz.product.id,
                            }
                            # wiz.create_invoice_line(vals)
                            self.create_invoice_line(new_cursor, uid, [ids[0]], vals)
                if not pre_calc:
                    inv_obj.button_reset_taxes(new_cursor, uid, [inv_id])
                    inv = inv_obj.browse(new_cursor, uid, inv_id)
                    inv_obj.write(new_cursor, uid, inv_id, {"check_total": inv.amount_total})
                    new_cursor.commit()

        if pre_calc:
            out = {"err": "", "calc": ""}
            for key in msg:
                for t in ("err", "calc"):
                    if msg[key][t]:
                        out[t] += "* Compte %s\n" % key
                        out[t] += "\n".join(msg[key][t])
                        out[t] += "\n  %s\n" % ("-" * 75)
            # wiz.write({'err': out['err'], 'calc': out['calc'],
            self.write(
                new_cursor,
                uid,
                [ids[0]],
                {"err": out["err"], "calc": out["calc"], "state": "pre_calc"},
            )
            logger.notifyChannel(
                "liquidacio APO",
                netsvc.LOG_INFO,
                _(u"Pre calc: err:{0} out:{1}).").format(out["err"], out["calc"]),
            )
            new_cursor.commit()
            new_cursor.close()
        else:
            new_cursor.close()
            return {
                "domain": "[('id','in', %s)]" % str(inv_ids),
                "name": _("Factures generades"),
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "account.invoice",
                "type": "ir.actions.act_window",
            }


WizardLiquidacioInteressos()
