# coding=utf-8
from osv import osv
from datetime import date, timedelta, datetime
import logging


class payment_order(osv.osv):

    _name = "payment.order"
    _inherit = "payment.order"

    def add_invoices_to_payment_order(
        self, cursor, uid, mode_pagament_id, data_venciment, context=None
    ):
        """
        Afegeix factures a la remesa amb mode de pagament `mode_pagament` que
        estigui en estat 'obert' o en 'esborrany'. Si no hi ha cap remesa que
        compleixi amb les anteriors condicions, llavors la crea.

        Les factures que s'afegeixen són totes aquelles que NO estan
        relacionades a cap remesa i en el que la seva data de venciment es
        igual o anterior a `data_venciment`.
        :param cursor: DB cursor.
        :type cursor: sql_db.Cursor
        :param uid:
        :param mode_pagament_id: Identificador del mode de pagament de la remesa.
        :type mode_pagament_id: int
        :param data_venciment: format: yyyy-mm-dd
        :param context: OpenERP context.
        :type context: dict
        :return: Tupla on el primer valor és el nombre de factures que s'han
        afegit a la remesa, on el segon valor indica l'identificador de la
        remesa afectada i el tercer indica si la remesa és nova.
        :rtype: (int, int, bool)
        """
        if context is None:
            context = {}
        factura_o = self.pool.get("giscedata.facturacio.factura")
        wiz_afegir_a_remesa_o = self.pool.get("wizard.afegir.factures.remesa")
        imd_obj = self.pool.get("ir.model.data")

        df_pending_state_id = imd_obj.get_object_reference(
            cursor, uid, "account_invoice_pending", "default_invoice_pending_state"
        )[1]

        bs_pending_state_id = imd_obj.get_object_reference(
            cursor,
            uid,
            "giscedata_facturacio_comer_bono_social",
            "correct_bono_social_pending_state",
        )[1]

        correct_ids = [df_pending_state_id, bs_pending_state_id]
        from_date_due = datetime.strptime(data_venciment, "%Y-%m-%d") - timedelta(days=7)
        from_date_due = from_date_due.strftime("%Y-%m-%d")
        dmn = [
            ("date_due", "<=", data_venciment),
            ("date_due", ">=", from_date_due),
            ("payment_order_id", "=", False),
            ("pending_state", "in", correct_ids),
            ("type", "like", "out_%"),
            ("invoice_id.payment_type.code", "=", "RECIBO_CSB"),
            ("group_move_id", "=", False),
            ("rectificative_type", "in", ("N", "C", "G")),
            ("state", "in", ("draft", "open")),
        ]
        factura_ids = factura_o.search(cursor, uid, dmn, context=context)
        remesa_created = False
        remesa_id = False

        if factura_ids:
            dmn = [
                ("mode", "=", mode_pagament_id),
                ("state", "in", ("draft", "open")),
                ("type", "=", "receivable"),
            ]
            remesa_id = self.search(cursor, uid, dmn, context=context)

            if remesa_id:
                if len(remesa_id) == 1:
                    remesa_id = remesa_id[0]
                else:
                    raise NotImplementedError
            else:
                remesa_cv = {
                    "mode": mode_pagament_id,
                    "date_prefered": "fixed",
                    "type": "receivable",
                }
                ctx = context.copy()
                ctx["type"] = "receivable"
                remesa_id = self.create(cursor, uid, remesa_cv, context=ctx)
                remesa_created = True

            ctx = context.copy()
            ctx["model"] = "giscedata.facturacio.factura"
            ctx["active_ids"] = factura_ids
            wiz_afegir_a_remesa_cv = {"order": remesa_id}
            wiz_afegir_a_remesa_id = wiz_afegir_a_remesa_o.create(
                cursor, uid, wiz_afegir_a_remesa_cv, context=ctx
            )
            wiz_afegir_a_remesa_o.action_afegir_factures(
                cursor, uid, wiz_afegir_a_remesa_id, context=ctx
            )

        return len(factura_ids), remesa_id, remesa_created

    def _cronjob_remesa_automatica(self, cursor, uid, context=None):
        """
        Funció per cridar des del cron. Afegeix automaticament factures a la
        remesa amb mode de pagament 'ENGINYERS'.

        Les factures que s'afegeixen són aquelles les quals la seva data de
        venciment es demà o abans de demà i no tenen cap remesa associada.
        :param cursor: DB cursor.
        :type cursor: sql_db.Cursor
        :param uid: usuari que executa l'acció.
        :type uid: int
        :param context: OpenERP context.
        :type context: dict
        :return: True si no hi ha hagut cap problema.
        """
        irmd_o = self.pool.get("ir.model.data")

        logger = logging.getLogger("openerp.payment.order.remesa_automatica")
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        mode_pagament_id = irmd_o.get_object_reference(
            cursor, uid, "som_extend_facturacio_comer", "payment_mode_remesa_automatica"
        )[1]
        res = self.add_invoices_to_payment_order(
            cursor, uid, mode_pagament_id, tomorrow, context=context
        )
        payment_order_created_txt = "Existing"

        if res[2]:
            payment_order_created_txt = "New"

        message_to_log = "{} facturas added. Affected payment order: {} ({})".format(
            res[0], res[1], payment_order_created_txt
        )
        logger.info(message_to_log)
        return True


payment_order()
