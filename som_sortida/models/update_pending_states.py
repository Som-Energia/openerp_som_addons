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

    def _update_polisses(self, cursor, uid, context=None):

        if context is None:
            context = {}
        logger = logging.getLogger('openerp.crontab.update_polisses')
        polissa_obj = self.pool.get('giscedata.polissa')
        logger.info('get_polisses_to_update called')
        polissa_ids = self.get_polisses_to_update(cursor, uid)
        logger.info('get_polisses_to_update returned {} polisses'.format(len(polissa_ids)))

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

    def get_polisses_to_update(self, cursor, uid):
        polissa_obj = self.pool.get('giscedata.polissa')
        search_params = [('sortida_state_id.weight', '>', 0),
                         ('sortida_state_id.pending_days', '>', 0)]
        return polissa_obj.search(cursor, uid, search_params)


UpdatePendingStates()
