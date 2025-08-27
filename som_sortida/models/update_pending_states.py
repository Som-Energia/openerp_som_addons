# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date

from osv import osv
import logging
import pooler


class UpdatePendingStates(osv.osv_memory):

    _inherit = 'update.pending.states'

    def update_state(self, cursor, uid, polissa_id, history_values, context=None):
        """
        If the pending days have passed, the pending_state of the polissa
        will change
        :param polissa_id: id of the polissa
        :param history_values: values of the pending history line
        """
        pstate_obj = self.pool.get('som.sortida.state')
        polissa_obj = self.pool.get('giscedata.polissa')

        fields_to_read = ['pending_days', 'is_last', 'pending_days_type']
        pstate = pstate_obj.read(
            cursor, uid, history_values['pending_state_id'], fields_to_read
        )
        change_date = datetime.strptime(
            history_values['change_date'], '%Y-%m-%d'
        ).date()
        current_date = date.today()

        if pstate['pending_days_type'] == 'business':
            from workalendar.europe import Spain
            due_date = Spain().add_working_days(
                change_date, pstate['pending_days']
            )
        else:
            due_date = (change_date + timedelta(days=pstate['pending_days']))

        if current_date >= due_date and not pstate['is_last']:
            polissa_obj.go_on_pending(cursor, uid, [polissa_id])

    def update_polisses(self, cursor, uid, context=None):
        self._update_polisses(cursor, uid, context=context)
        self._send_pending_emails_and_update_states(cursor, uid, context=context)

    def _update_polisses(self, cursor, uid, context=None):

        if context is None:
            context = {}
        logger = logging.getLogger('openerp.crontab.update_polisses')
        polissa_obj = self.pool.get('giscedata.polissa')
        logger.info('_get_polisses_to_update called')
        polissa_ids = self._get_polisses_to_update(cursor, uid)
        logger.info('_get_polisses_to_update returned {} polisses'.format(len(polissa_ids)))

        db = pooler.get_db(cursor.dbname)
        last_lines_by_polissa = {}
        for polissa_id in polissa_ids:
            tmp_cursor = db.cursor()
            logger.info(
                'get_current_pending_state_info called for polissa with id {}'.format(polissa_id))
            try:
                last_lines_by_polissa.update(
                    polissa_obj.get_current_pending_state_info(
                        tmp_cursor, uid, polissa_id, context=context
                    )
                )
                tmp_cursor.commit()
                logger.info(
                    'get_current_pending_state_info succeed \
                        for polissa with id {}'.format(polissa_id))
            except Exception:
                tmp_cursor.rollback()
                logger.info(
                    'get_current_pending_state_info failed \
                        for polissa with id {}'.format(polissa_id))
            finally:
                tmp_cursor.close()

        for polissa_id, history_values in last_lines_by_polissa.items():
            tmp_cursor = db.cursor()
            logger.info('update_state called for polissa with id {}'.format(polissa_id))
            try:
                self.update_state(tmp_cursor, uid, polissa_id, history_values)
                tmp_cursor.commit()
                logger.info('update_state succeed for polissa with id {}'.format(polissa_id))
            except Exception:
                tmp_cursor.rollback()
                logger.info('update_state failed for polissa with id {}'.format(polissa_id))
            finally:
                tmp_cursor.close()

        return True

    def _get_polisses_to_update(self, cursor, uid):
        polissa_obj = self.pool.get('giscedata.polissa')
        search_params = [('sortida_state_id.weight', '>', 0),
                         ('sortida_state_id.pending_days', '>', 0)]
        return polissa_obj.search(cursor, uid, search_params)

    def _send_pending_emails_and_update_states(self, cursor, uid, context=None):
        logger = logging.getLogger("openerp.poweremail")
        polissa_obj = self.pool.get('giscedata.polissa')
        polissa_ids = polissa_obj.search(cursor, uid, [
            ('sortida_state_id.weight', '>', 0),
            ('sortida_state_id.template_id', '!=', False),
        ])

        for polissa in polissa_obj.browse(cursor, uid, polissa_ids):
            ret_value = self._send_polissa_email(
                cursor, uid, polissa.id, polissa.sortida_state_id.template_id
            )

            if ret_value == -1:
                logger.info(
                    "ERROR: Sending email for {polissa_id} polissa error.".format(
                        polissa_id=polissa.id,
                    )
                )
            else:
                polissa_obj.go_on_pending(cursor, uid, [polissa.id])
                logger.info(
                    "Sending email for {polissa_id} polissa with result: {ret_value}".format(
                        polissa_id=polissa.id, ret_value=ret_value
                    )
                )

    def _send_polissa_email(self, cursor, uid, polissa_id, template):
        logger = logging.getLogger("openerp.poweremail")

        try:
            wiz_send_obj = self.pool.get("poweremail.send.wizard")
            ctx = {
                "active_ids": [polissa_id],
                "active_id": polissa_id,
                "template_id": template.id,
                "src_model": "giscedata.polissa",
                "src_rec_ids": [polissa_id],
                "from": template.enforce_from_account.id,
                "state": "single",
                "priority": "0",
            }

            params = {"state": "single", "priority": "0", "from": ctx["from"]}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            return wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            logger.info(
                "ERROR sending email to polissa {polissa_id}: {exc}".format(
                    polissa_id=polissa_id, exc=e.message
                )
            )
            return -1


UpdatePendingStates()
