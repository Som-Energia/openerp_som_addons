# -*- coding: utf-8 -*-

from datetime import date

from osv import osv, fields
from tools.translate import _


class WizardInvestmentActivation(osv.osv_memory):

    _name = 'wizard.generationkwh.investment.activation'

    def do_action(self, cursor, uid, ids, context=None):
        """ Do selected action"""
        if context is None:
            context = {}

        Investment = self.pool.get('generationkwh.investment')
        Member = self.pool.get('somenergia.soci')

        wiz = self.browse(cursor, uid, ids[0], context=context)

        action = wiz.action
        action_name = (action == 'activate' and _('Activat') or _('Desactivat'))

        inv_ids = context.get('active_ids', [])

        for inv_id in inv_ids:
            if action == 'activate':
                Investment.activate(cursor, uid, inv_id, context)
            else:
                Investment.deactivate(cursor, uid, inv_id, context)

        txt = _("S'han {0} {1} inversions").format(
            action_name, len(inv_ids)
        )

        wiz.write({'info': txt}, context=context)

    def _default_action(self, cursor, uid, context=None):
        """Gets wizard action from context"""
        if context is None:
            context = {}

        action = context.get('action', False)

        if action:
            return action

        investment_ids = context.get('active_ids', False)

        if len(investment_ids) == 1:
            # Only 1 investment
            inv_obj = self.pool.get('generationkwh.investment')
            is_active = inv_obj.read(
                cursor, uid, investment_ids[0], ['active'], context
            )['active']
            if is_active:
                return 'deactivate'
            else:
                return 'activate'
        else:
            return ''

    def _default_info(self, cursor, uid, context=None):
        """Fills wizard info field depending on action/investments selected"""
        action = self._default_action(cursor, uid, context=context)
        change_date = date.today()
        investment_id = context.get('active_id')
        if action == 'activate':
            info_txt = _(
                u"S'activarà la inversió {0} amb data {1}"
            ).format(investment_id, change_date)
        elif action == 'deactivate':
            info_txt = _(
                u"Es desactivarà la inversió {0} amb data {1}"
            ).format(investment_id, change_date)
        else:
            info_txt = _(
                u"Escull la acció que vols realitzar sobre les "
                u"{0} inversions seleccionades amb data {1}. Només "
                u"es canviaràn les que estiguin en l'estat addient"
            ).format(len(context.get('active_ids', [])), change_date)
        return info_txt

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'action': fields.selection([
			('activate', 'Activa'),
			('deactivate', 'Desactiva')
			],
            string='Action'
        )
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': _default_info,
        'action': _default_action,
    }

WizardInvestmentActivation()
