# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

STATES = [
    ('init', 'Estat Inicial'),
    ('finished', 'Estat Final'),
]

class WizardSendReports(osv.osv_memory):
    _name = 'wizard.infoenergia.send.reports'

    def _get_lot_id(self,cursor, uid, context):
        if context is None:
            return False

        if context.get('from_model') == 'som.infoenergia.lot.enviament':
            lot_id = context.get('active_id', 0)

        elif context.get('from_model') == 'som.infoenergia.enviament':
            env_obj = self.pool.get('som.infoenergia.enviament')
            env_id = context.get('active_id', 0)
            lot_id = env_obj.read(cursor, uid, env_id, ['lot_enviament'])['lot_enviament'][0]
        return lot_id

    def _get_is_test(self, cursor, uid, context=None):

        lot_id = self._get_lot_id(cursor, uid, context)
        lot_obj = self.pool.get('som.infoenergia.lot.enviament')

        return lot_obj.read(cursor, uid, lot_id,['is_test'])['is_test']

    def _get_default_subject(self, cursor, uid, context=None):

        lot_id = self._get_lot_id(cursor, uid, context)
        lot_obj = self.pool.get('som.infoenergia.lot.enviament')

        lot = lot_obj.browse(cursor, uid, lot_id)
        return lot.email_template.def_subject

    def send_reports(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context=context)
        env_obj = self.pool.get('som.infoenergia.enviament')

        ctx = {'allow_reenviar': wiz.allow_reenviar}
        if wiz.is_test:
            if not wiz.email_to:
                raise osv.except_osv(_(u'ERROR'), "Cal indicar l'email destinatari de l'enviament")

            ctx.update({'email_to': wiz.email_to, 'email_subject': wiz.email_subject})

        env_ids = []
        if context.get('from_model') == 'som.infoenergia.lot.enviament':
            lot_id = context.get('active_id', 0)
            env_ids = env_obj.search(cursor, uid, [('lot_enviament', '=', lot_id)])
        elif context.get('from_model') == 'som.infoenergia.enviament':
            env_ids = context.get('active_ids', [])

        wiz.write({'state': "finished"})

        env_obj.send_reports(cursor, uid, env_ids, context=ctx)

    _columns = {
        'state': fields.selection(STATES, _(u"Estat del wizard d'enviament del lot de reports")),
        'is_test': fields.boolean('Test', help=_(u"És un lot de Test?")),
        'email_to': fields.char(u'E-mail on enviar els correus', size=256, help=u"Tots els enviaments s'enviaran a aquesta adreça"),
        'email_subject': fields.char('Assumpte correu', size=200, help="Assumpte dels correus enviats"),
        'allow_reenviar': fields.boolean('Reenviar correus ja enviats', help=_(u"Permetre que es reenviïn correus ja enviats?")),
    }

    _defaults = {
        'state': 'init',
        'is_test': _get_is_test,
        'email_subject': _get_default_subject,
        'allow_reenviar': lambda *a: False,
    }


WizardSendReports()
