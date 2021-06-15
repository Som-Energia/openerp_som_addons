# -*- coding: utf-8 -*-
from osv import osv
from som_account_invoice_pending_exceptions import (
    UpdateWaitingFor48hException,
    UpdateWaitingCancelledContractsException,
    UpdateWaitingForAnnexIVException,
    MailException,
    SMSException
)
import logging

class UpdatePendingStates(osv.osv_memory):
    _name = 'update.pending.states'
    _inherit = 'update.pending.states'

    def update_invoices(self, cursor, uid, context=None):
        super(UpdatePendingStates,
              self).update_invoices(cursor, uid, context=context)
        self.update_second_unpaid_invoice(cursor, uid)
        self.update_waiting_for_annexII(cursor, uid)
        self.update_waiting_for_annexIII_first(cursor, uid)
        self.update_waiting_for_annexIII_second(cursor, uid)
        self.update_waiting_for_annexIV(cursor, uid)
        self.update_waiting_for_48h(cursor, uid)

    def get_object_id(self, cursor, uid, module, sem_id):
        """
        Return id of the state corresponding to the module and sem_id given
        """
        ir_model_data = self.pool.get('ir.model.data')
        return ir_model_data.get_object_reference(
            cursor, uid, module, sem_id
        )[1]

    def get_invoices_with_pending_state(self, cursor, uid, pending_state):
        """
        Return invoices (giscedata factura) with the given pending state
        """
        fact_obj = self.pool.get('giscedata.facturacio.factura')

        inv_obj = self.pool.get('account.invoice')
        invoice_ids = inv_obj.search(cursor, uid, [('pending_state.id', '=', pending_state)], order='id asc')

        invoice_numbers = [inv_obj.browse(cursor, uid, inv_id).number for inv_id in invoice_ids]
        factura_ids = []
        if invoice_numbers:
            factura_ids = fact_obj.search(cursor, uid, [("number", "in", invoice_numbers)], order='id asc')

        return factura_ids

    def get_from_email(self, cursor, uid, template_id):
        """
        Return email from poweremail template
        """
        account_obj = self.pool.get('poweremail.core_accounts')
        power_email_tmpl_obj = self.pool.get('poweremail.templates')

        template = power_email_tmpl_obj.read(cursor, uid, template_id)

        email_from = False
        template_name = 'Gestió de Cobraments'

        if template.get(template_name):
            email_from = template.get('enforce_from_account')[0]

        if not email_from:
            email_from = account_obj.search(cursor, uid, [('name', '=', template_name)])[0]

        return email_from

    def send_email(self, cursor, uid, factura_id, email_params):
        logger = logging.getLogger('openerp.poweremail')

        try:
            wiz_send_obj = self.pool.get('poweremail.send.wizard')
            ctx = {
                'active_ids': [factura_id],
                'active_id': factura_id,
                'template_id': email_params['template_id'],
                'src_model': 'giscedata.facturacio.factura',
                'src_rec_ids': [factura_id],
                'from': email_params['email_from'],
                'state': 'single',
                'priority': '0',
            }

            params = {'state': 'single', 'priority': '0', 'from': ctx['from']}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            return wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            logger.info(
                'ERROR sending email to invoice {factura_id}: {exc}'.format(
                    factura_id=factura_id,
                    exc=e
                )
            )
            return -1

    def send_sms(self, cursor, uid, factura_id, template_id, pending_state, context=None):
        logger = logging.getLogger('openerp.powersms')

        try:
            template_obj = self.pool.get('powersms.templates')
            template = template_obj.browse(cursor, uid, template_id)
            wiz_send_obj = self.pool.get('powersms.send.wizard')
            params = {
                'account': template.enforce_from_account.id,
            }
            create_empty_number = context.get('create_empty_number', False)
            ctx = {
                'active_ids': [factura_id],
                'active_id': factura_id,
                'template_id': template_id,
                'src_model': 'giscedata.facturacio.factura',
                'src_rec_ids': [factura_id],
                'pending_state_id': pending_state,
                'create_empty_number': create_empty_number,
            }
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)

            return wiz_send_obj.send_sms(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            logger.info(
                'ERROR sending sms to invoice {factura_id}: {exc}'.format(
                    factura_id=factura_id,
                    exc=e
                )
            )
            raise e

    def update_waiting_for_48h(self, cursor, uid, context=None):
        logger = logging.getLogger(__name__)

        if context is None:
            context = {}

        # DEFAULT PROCESS
        waiting_48h_dp = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'default_pendent_notificacio_tall_imminent_pending_state'
        )
        sent_48h_dp = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'default_notificacio_tall_imminent_enviada_pending_state'
        )
        traspas_advocats_dp = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'default_pendent_traspas_advocats_pending_state'
        )

        factura_dp_ids = self.get_invoices_with_pending_state(cursor, uid, waiting_48h_dp)
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        pol_obj = self.pool.get('giscedata.polissa')

        polisses_factures = {}

        for factura_id in sorted(factura_dp_ids):
            invoice = fact_obj.read(cursor, uid, factura_id, ['id', 'polissa_id'])
            polissa_id = invoice['polissa_id'][0]
            polissa_state = pol_obj.read(cursor, uid, polissa_id, ['state'])['state']

            try:
                if polissa_state == 'baixa':
                    self.update_waiting_for_annex_cancelled_contracts(cursor, uid, factura_id, traspas_advocats_dp, context)
                else:
                    if polissa_id in polisses_factures:
                        ctx = context.copy()
                        ctx['related_invoice'] = polisses_factures[polissa_id]
                        self.update_waiting_for_48h_active_contracts(cursor, uid, factura_id, sent_48h_dp, ctx)
                    else:
                        polisses_factures[polissa_id] = factura_id
                        self.update_waiting_for_48h_active_contracts(cursor, uid, factura_id, sent_48h_dp, context)
            except UpdateWaitingFor48hException as e:
                logger.info(
                    'ERROR updating invoice {factura_id} in update_waiting_for_48h: {exc}'.format(
                        factura_id=factura_id,
                        exc=e.message
                    )
                )
            except UpdateWaitingCancelledContractsException as e:
                logger.info(
                    'ERROR updating invoice {factura_id} in update_waiting_for_48h: {exc}'.format(
                        factura_id=factura_id,
                        exc=e.message
                    )
                )
            except Exception as e:
                logger.info(
                    'UNHANDLED ERROR updating invoice {factura_id} in update_waiting_for_48h: {exc}'.format(
                        factura_id=factura_id,
                        exc=e.message
                    )
                )


        # BO SOCIAL
        waiting_48h_bs = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'pendent_notificacio_tall_imminent_pending_state'
        )
        sent_48h_bs = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'notificacio_tall_imminent_enviada_pending_state'
        )
        traspas_advocats_bs = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'pendent_traspas_advocats_pending_state'
        )
        factura_bs_ids = self.get_invoices_with_pending_state(cursor, uid, waiting_48h_bs)


        for factura_id in sorted(factura_bs_ids):
            invoice = fact_obj.read(cursor, uid, factura_id, ['id', 'polissa_id'])
            polissa_id = invoice['polissa_id'][0]
            polissa_state = pol_obj.read(cursor, uid, polissa_id, ['state'])['state']
            try:
                if polissa_state == 'baixa':
                    self.update_waiting_for_annex_cancelled_contracts(cursor, uid, factura_id, traspas_advocats_bs, context)
                else:
                    if polissa_id in polisses_factures:
                        ctx = context.copy()
                        ctx['related_invoice'] = polisses_factures[polissa_id]
                        self.update_waiting_for_48h_active_contracts(cursor, uid, factura_id, sent_48h_bs, ctx)
                    else:
                        polisses_factures[polissa_id] = factura_id
                        self.update_waiting_for_48h_active_contracts(cursor, uid, factura_id, sent_48h_bs, context)
            except UpdateWaitingFor48hException as e:
                logger.info(
                    'ERROR updating invoice {factura_id} in update_waiting_for_48h: {exc}'.format(
                        factura_id=factura_id,
                        exc=e.message
                    )
                )
            except UpdateWaitingCancelledContractsException as e:
                logger.info(
                    'ERROR updating invoice {factura_id} in update_waiting_for_48h: {exc}'.format(
                        factura_id=factura_id,
                        exc=e.message
                    )
                )
            except Exception as e:
                logger.info(
                    'UNHANDLED ERROR updating invoice {factura_id} in update_waiting_for_48h: {exc}'.format(
                        factura_id=factura_id,
                        exc=e.message
                    )
                )

    def update_waiting_for_48h_active_contracts(self, cursor, uid, factura_id, next_state, context=None):
        logger = logging.getLogger('openerp.poweremail')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        aiph_obj = self.pool.get('account.invoice.pending.history')

        try:
            related_invoice = context.get('related_invoice', False)

            mail_48h_template_id = self.get_object_id(
                cursor, uid, 'som_account_invoice_pending', 'email_impagats_48h'
            )

            email_from = self.get_from_email(cursor, uid, mail_48h_template_id)

            sms_48h_template_id = self.get_object_id(
                cursor, uid, 'som_account_invoice_pending', 'sms_template_48h_tall'
            )

            current_state_id = fact_obj.read(cursor, uid, factura_id, ['pending_state'])['pending_state'][0]

            email_params = dict({
                'email_from': email_from,
                'template_id': mail_48h_template_id
            })

            ret_value = self.send_email(cursor, uid, factura_id, email_params)

            if ret_value == -1:
                logger.info(
                    'ERROR: Sending 48h email for {factura_id} invoice error.'.format(
                        factura_id=factura_id,
                    )
                )
            else:
                if not related_invoice:
                    try:
                        self.send_sms(cursor, uid, factura_id, sms_48h_template_id, current_state_id, context)
                    except Exception as e:
                        raise SMSException(e)
                else:
                    last_peding_id = max(fact_obj.read(cursor, uid, factura_id, ['pending_history_ids'])['pending_history_ids'])
                    last_pending = aiph_obj.browse(cursor, uid, last_peding_id)
                    last_pending.historize(message=u"Comunicació feta a través de la factura amb id:{}".format(related_invoice))
                fact_obj.set_pending(cursor, uid, [factura_id], next_state)
                logger.info(
                    'Sending 48h email for {factura_id} invoice with result: {ret_value}'.format(
                        factura_id=factura_id,
                        ret_value=ret_value
                    )
                )
        except Exception as e:
            raise UpdateWaitingFor48hException(e)

    def update_waiting_for_annexIV(self, cursor, uid, context=None):
        """
        If exists one invoice with state corresponding to default_pendent_carta_avis_tall_pending_state id,
        automatically will send it's corresponding email and pass to next
        pending state (default_carta_avis_tall_pending_state)
        """
        logger = logging.getLogger(__name__)

        if context is None:
            context = {}

        # DEFAULT PROCESS
        waiting_annexIV_dp = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'default_pendent_carta_avis_tall_pending_state'
        )
        sent_annexIV_dp = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'default_carta_avis_tall_pending_state'
        )
        traspas_advocats_dp = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'default_pendent_traspas_advocats_pending_state'
        )

        factura_dp_ids = self.get_invoices_with_pending_state(cursor, uid, waiting_annexIV_dp)
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        pol_obj = self.pool.get('giscedata.polissa')

        polisses_factures = {}

        for factura_id in sorted(factura_dp_ids):
            try:
                invoice = fact_obj.read(cursor, uid, factura_id, ['id', 'polissa_id'])
                polissa_id = invoice['polissa_id'][0]
                polissa_state = pol_obj.read(cursor, uid, polissa_id, ['state'])['state']
                if polissa_state == 'baixa':
                    self.update_waiting_for_annex_cancelled_contracts(cursor, uid, factura_id, traspas_advocats_dp, context)
                else:
                    if polissa_id in polisses_factures:
                        ctx = context.copy()
                        ctx['related_invoice'] = polisses_factures[polissa_id]
                        self.update_waiting_for_annexIV_active_contracts(cursor, uid, factura_id, sent_annexIV_dp, ctx)
                    else:
                        polisses_factures[polissa_id] = factura_id
                        self.update_waiting_for_annexIV_active_contracts(cursor, uid, factura_id, sent_annexIV_dp, context)

            except UpdateWaitingForAnnexIVException as e:
                logger.info(
                    'ERROR updating invoice {factura_id} in update_waiting_for_annexIV: {exc}'.format(
                        factura_id=factura_id,
                        exc=e
                    )
                )
            except UpdateWaitingCancelledContractsException as e:
                logger.info(
                    'ERROR updating invoice {factura_id} in update_waiting_for_annexIV: {exc}'.format(
                        factura_id=factura_id,
                        exc=e
                    )
                )
            except Exception as e:
                logger.info(
                    'UNHANDLED ERROR updating invoice {factura_id} in update_waiting_for_annexIV: {exc}'.format(
                        factura_id=factura_id,
                        exc=e
                    )
                )


        # BO SOCIAL
        waiting_annexIV_bs = self.get_object_id(
            cursor, uid, 'giscedata_facturacio_comer_bono_social', 'pendent_carta_avis_tall_pending_state'
        )
        sent_annexIV_bs = self.get_object_id(
            cursor, uid, 'giscedata_facturacio_comer_bono_social', 'carta_avis_tall_pending_state'
        )
        traspas_advocats_bs = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'pendent_traspas_advocats_pending_state'
        )
        factura_bs_ids = self.get_invoices_with_pending_state(cursor, uid, waiting_annexIV_bs)

        for factura_id in sorted(factura_bs_ids):
            invoice = fact_obj.read(cursor, uid, factura_id, ['id', 'polissa_id'])
            polissa_id = invoice['polissa_id'][0]
            polissa_state = pol_obj.read(cursor, uid, polissa_id, ['state'])['state']
            try:
                if polissa_state == 'baixa':
                    self.update_waiting_for_annex_cancelled_contracts(cursor, uid, factura_id, traspas_advocats_bs, context)
                else:
                    if polissa_id in polisses_factures:
                        ctx = context.copy()
                        ctx['related_invoice'] = polisses_factures[polissa_id]
                        self.update_waiting_for_annexIV_active_contracts(cursor, uid, factura_id, sent_annexIV_bs, ctx)
                    else:
                        polisses_factures[polissa_id] = factura_id
                        self.update_waiting_for_annexIV_active_contracts(cursor, uid, factura_id, sent_annexIV_bs, context)

            except UpdateWaitingForAnnexIVException as e:
                logger.info(
                    'ERROR updating invoice {factura_id} in update_waiting_for_annexIV: {exc}'.format(
                        factura_id=factura_id,
                        exc=e
                    )
                )
            except UpdateWaitingCancelledContractsException as e:
                logger.info(
                    'ERROR updating invoice {factura_id} in update_waiting_for_annexIV: {exc}'.format(
                        factura_id=factura_id,
                        exc=e
                    )
                )
            except Exception as e:
                logger.info(
                    'UNHANDLED ERROR updating invoice {factura_id} in update_waiting_for_annexIV: {exc}'.format(
                        factura_id=factura_id,
                        exc=e
                    )
                )


    def update_waiting_for_annexIII_first(self, cursor, uid, context=None):
        """
        If exists one invoice with state corresponding to waiting_annexIII_first,
        automatically will send it's corresponding email and pass to next
        pending state annexIII_first_sent
        """
        if context is None:
            context = {}

        waiting_annexIII_first = self.get_object_id(
            cursor, uid, 'giscedata_facturacio_comer_bono_social', 'carta_1_pendent_pending_state'
        )
        annexIII_first_sent = self.get_object_id(
            cursor, uid, 'giscedata_facturacio_comer_bono_social', 'carta_1_pending_state'
        )
        self.update_update_waiting_for_annexIII(cursor, uid, waiting_annexIII_first, annexIII_first_sent, context)

    def update_waiting_for_annexIII_second(self, cursor, uid, context=None):
        """
        If exists one invoice with state corresponding to waiting_annexIII_second id,
        automatically will send it's corresponding email and pass to next
        pending state annexIII_second_sent
        """
        if context is None:
            context = {}

        waiting_annexIII_second = self.get_object_id(
            cursor, uid, 'giscedata_facturacio_comer_bono_social', 'carta_2_pendent_pending_state'
        )
        annexIII_second_sent = self.get_object_id(
            cursor, uid, 'giscedata_facturacio_comer_bono_social', 'carta_2_pending_state'
        )
        self.update_update_waiting_for_annexIII(cursor, uid, waiting_annexIII_second, annexIII_second_sent, context)



    def update_update_waiting_for_annexIII(self, cursor, uid, initial_state, final_state, context=None):
        """
        If exists one invoice with state corresponding to initial_state id,
        automatically will send email_impagats_annex3 email and pass to final_state
        """
        if context is None:
            context = {}
        logger = logging.getLogger('openerp.poweremail')

        template_id = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'email_impagats_annex3'
        )

        email_from = self.get_from_email(cursor, uid, template_id)

        factura_ids = self.get_invoices_with_pending_state(cursor, uid, initial_state)
        fact_obj = self.pool.get('giscedata.facturacio.factura')

        email_params = dict({
            'email_from': email_from,
            'template_id': template_id
        })

        for factura_id in factura_ids:
            invoice = fact_obj.read(cursor, uid, factura_id)
            ret_value = self.send_email(cursor, uid, invoice['id'], email_params)

            if ret_value == -1:
                logger.info(
                    'ERROR: Sending Annex 3 first email to {invoice_name} partner error.'.format(
                        invoice_name=invoice['partner_id'][1],
                    )
                )
            else:
                fact_obj.set_pending(cursor, uid, [factura_id], final_state)
                logger.info(
                    'Sending Annex 3 first email to {invoice_name} partner with result: {ret_value}'.format(
                        invoice_name=invoice['partner_id'][1],
                        ret_value=ret_value
                    )
                )

    def update_waiting_for_annexII(self, cursor, uid, context=None):
        """
        If exists one invoice with state corresponding to waiting_annexII id,
        automatically will send it's corresponding email and pass to next
        pending state (sent_annexII)
        """
        if context is None:
            context = {}


        waiting_annexII = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'pendent_avis_previ_inici_procediment_pending_state'
        )
        traspas_advocats_bs = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'pendent_traspas_advocats_pending_state'
        )

        factura_ids = self.get_invoices_with_pending_state(cursor, uid, waiting_annexII)
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        pol_obj = self.pool.get('giscedata.polissa')

        for factura_id in factura_ids:
            invoice = fact_obj.read(cursor, uid, factura_id, ['id', 'polissa_id'])
            polissa_id = invoice['polissa_id'][0]
            polissa_state = pol_obj.read(cursor, uid, polissa_id, ['state'])['state']

            if polissa_state == 'baixa':
                self.update_waiting_for_annex_cancelled_contracts(cursor, uid, factura_id, traspas_advocats_bs, context)
            else:
                self.update_waiting_for_annexII_active_contracts(cursor, uid, factura_id, context)


    def update_waiting_for_annex_cancelled_contracts(self, cursor, uid, factura_id, next_state, context=None):
        logger = logging.getLogger('openerp.poweremail')
        fact_obj = self.pool.get('giscedata.facturacio.factura')

        try:
            n57_template_id = self.get_object_id(
                cursor, uid, 'som_account_invoice_pending', 'email_generic_N57'
            )

            email_from = self.get_from_email(cursor, uid, n57_template_id)

            email_params = dict({
                'email_from': email_from,
                'template_id': n57_template_id
            })

            ret_value = 1 #self.send_email(cursor, uid, factura_id, email_params)

            if ret_value == -1:
                logger.info(
                    'ERROR: Sending N57 default payment email for {factura_id} invoice error.'.format(
                        factura_id=factura_id,
                    )
                )
            else:
                fact_obj.set_pending(cursor, uid, [factura_id], next_state)
                logger.info(
                    'Sending N57 default payment email for {factura_id} invoice with result: {ret_value}'.format(
                        factura_id=factura_id,
                        ret_value=ret_value
                    )
                )
        except Exception as e:
            raise UpdateWaitingCancelledContractsException(e)

    def update_waiting_for_annexII_active_contracts(self, cursor, uid, factura_id, context=None):
        logger = logging.getLogger('openerp.poweremail')
        fact_obj = self.pool.get('giscedata.facturacio.factura')

        sent_annexII = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'avis_previ_inici_procediment_enviat_pending_state'
        )

        annex2_template_id = self.get_object_id(
            cursor, uid, 'som_account_invoice_pending', 'email_impagats_annex2'
        )

        email_from = self.get_from_email(cursor, uid, annex2_template_id)

        email_params = dict({
            'email_from': email_from,
            'template_id': annex2_template_id
        })

        ret_value = self.send_email(cursor, uid, factura_id, email_params)

        if ret_value == -1:
            logger.info(
                'ERROR: Sending Annex 2 email for {factura_id} invoice error.'.format(
                    factura_id=factura_id,
                )
            )
        else:
            fact_obj.set_pending(cursor, uid, [factura_id], sent_annexII)
            logger.info(
                'Sending Annex 2 email for {factura_id} invoice with result: {ret_value}'.format(
                    factura_id=factura_id,
                    ret_value=ret_value
                )
            )

    def update_waiting_for_annexIV_active_contracts(self, cursor, uid, factura_id, next_state, context=None):
        logger = logging.getLogger('openerp.poweremail')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        aiph_obj = self.pool.get('account.invoice.pending.history')

        try:
            related_invoice = context.get('related_invoice', False)

            annex4_template_id = self.get_object_id(
                cursor, uid, 'som_account_invoice_pending', 'email_impagats_annex4'
            )

            email_from = self.get_from_email(cursor, uid, annex4_template_id)

            sms_template_id = self.get_object_id(
                cursor, uid, 'som_account_invoice_pending', 'sms_template_annex4'
            )

            current_state_id = fact_obj.read(cursor, uid, factura_id, ['pending_state'])['pending_state'][0]

            email_params = dict({
                'email_from': email_from,
                'template_id': annex4_template_id
            })

            ret_value = self.send_email(cursor, uid, factura_id, email_params)

            if ret_value == -1:
                logger.info(
                    'ERROR: Sending Annex 4 email for {factura_id} invoice error.'.format(
                        factura_id=factura_id,
                    )
                )
            else:
                if not related_invoice:
                    try:
                        self.send_sms(cursor, uid, factura_id, sms_template_id, current_state_id, context)
                    except Exception as e:
                        raise SMSException(e)
                else:
                    last_peding_id = max(fact_obj.read(cursor, uid, factura_id, ['pending_history_ids'])['pending_history_ids'])
                    last_pending = aiph_obj.browse(cursor, uid, last_peding_id)
                    last_pending.historize(message=u"Comunicació feta a través de la factura amb id:{}".format(related_invoice))
                fact_obj.set_pending(cursor, uid, [factura_id], next_state)
                logger.info(
                    'Sending Annex 4 email for {factura_id} invoice with result: {ret_value}'.format(
                        factura_id=factura_id,
                        ret_value=ret_value
                    )
                )
        except Exception as e:
            raise UpdateWaitingForAnnexIVException(e)

    def update_second_unpaid_invoice(self, cursor, uid, context=None):

        if context is None:
            context = {}

        ir_model_data = self.pool.get('ir.model.data')

        # BO SOCIAL
        bs_correct_id = ir_model_data.get_object_reference(
            cursor, uid, 'giscedata_facturacio_comer_bono_social', 'correct_bono_social_pending_state'
        )[1]

        bs_waiting_unpaid_id = ir_model_data.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'esperant_segona_factura_impagada_pending_state'
        )[1]

        bs_waiting_notif_id = ir_model_data.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'pendent_notificacio_tall_imminent_pending_state'
        )[1]

        # DEFAULT PROCESS
        dp_correct_id = ir_model_data.get_object_reference(
            cursor, uid, 'account_invoice_pending', 'default_invoice_pending_state'
        )[1]

        dp_waiting_unpaid_id = ir_model_data.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'default_esperant_segona_factura_impagada_pending_state'
        )[1]

        dp_waiting_notif_id = ir_model_data.get_object_reference(
            cursor, uid, 'som_account_invoice_pending', 'default_pendent_notificacio_tall_imminent_pending_state'
        )[1]

        self.update_state_with_2_invoices_unpaid(cursor, uid, 'Bo Social', bs_correct_id, bs_waiting_unpaid_id, bs_waiting_notif_id, context)
        self.update_state_with_2_invoices_unpaid(cursor, uid, 'Default Process', dp_correct_id, dp_waiting_unpaid_id, dp_waiting_notif_id, context)


    def update_state_with_2_invoices_unpaid(self, cursor, uid, process_name, correct_id, waiting_unpaid_id, waiting_notif_id, context=None):
        """
        If exists one invoice with state corresponding to waiting_unpaid_id
        and at least two invoices between state corresponding to correct_id
        and waiting_notif_id, all are updated to the state corresponding
        to waiting_notif_id

        :param process_name: pending state process name
        :param correct_id: lowest weight in process
        :param waiting_unpaid_id: at least one invoice with this pstate
        :param waiting_notif_id: final state after update
        """
        if context is None:
            context = {}
        inv_obj = self.pool.get('account.invoice')
        fact_obj = self.pool.get('giscedata.facturacio.factura')
        pend_obj = self.pool.get('account.invoice.pending.state')
        waiting_unpaid_weight = pend_obj.browse(cursor, uid, waiting_unpaid_id).weight
        correct_weight = pend_obj.browse(cursor, uid, correct_id).weight

        invoice_ids = inv_obj.search(cursor, uid, [('pending_state.id', '=', waiting_unpaid_id),
                                                   ('pending_state.process_id.name', 'like', process_name)])

        for inv_id in invoice_ids:
            contract_name = inv_obj.read(cursor, uid, inv_id, ['name'])['name']
            inv_list = inv_obj.search(cursor, uid, [('name', 'like', contract_name),
                                                    ('pending_state.weight', '<=', waiting_unpaid_weight),
                                                    ('pending_state.weight', '>', correct_weight)])

            if len(inv_list) >= 2:
                for invoice_id in inv_list:
                    inv_number = inv_obj.browse(cursor, uid, invoice_id).number
                    fact_ids = fact_obj.search(cursor, uid, [('number', '=', inv_number)])
                    fact_obj.set_pending(cursor, uid, fact_ids, waiting_notif_id)


UpdatePendingStates()
