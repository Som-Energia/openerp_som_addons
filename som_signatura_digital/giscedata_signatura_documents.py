from osv import osv


class GiscedataSignaturaProcess(osv.osv):
    _inherit = 'giscedata.signatura.process'

    def remind_emails_cron(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        context['reminder'] = True

        super(GiscedataSignaturaProcess, self).remind_emails_cron(cursor, uid, ids, context=context)


GiscedataSignaturaProcess()
