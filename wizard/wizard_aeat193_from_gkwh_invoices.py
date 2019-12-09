# -*- encoding: utf-8 -*-
from osv import osv, fields


class WizardComputeMod193Invoice(osv.osv_memory):

    _name = 'wizard.aeat193.from.gkwh.invoices'

    def get_year(self, cursor, uid, context=None):
        if context is None:
            context = {}

        report_obj = self.pool.get('l10n.es.aeat.mod193.report')
        report_id = context.get('active_id')

        report = report_obj.browse(cursor, uid, report_id, context)

        return {
            'name': report.fiscalyear_id.name,
            'start': report.fiscalyear_id.date_start,
            'end': report.fiscalyear_id.date_stop
        }

    def _default_info(self, cursor, uid, context=None):
        if context is None:
            context = {}

        txt = u"Calculant la retenció de IRPF per a les factures amb " \
              u"Generation kWh de l'any {name} ({start}->{end}"

        dates = self.get_year(cursor, uid, context)

        res = txt.format(**dates)

        return res

    def do_action(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz_id = ids[0]
        wiz = self.browse(cursor, uid, wiz_id, context)

        report_obj = self.pool.get('l10n.es.aeat.mod193.report')
        report_id = context.get('active_id')

        report = report_obj.browse(cursor, uid, report_id, context)

        dates = self.get_year(cursor, uid, context)

        txt = u"Calculant linies del model 193 de la AEAT " \
              u"per l'any fiscal {name}\n" \
              u"Buscarem les factures entre les dates " \
              u"{start} i {end}".format(**dates)



        num_linies = 0
        num_factures = 0
        txt += u'Afegides {} línies de {} factures'.format(
            num_linies, num_factures
        )



        wiz.write(cursor, uid, wiz_id, {'info': txt})
        return True

    _columns = {
        'tax_id': fields.many2one(
            'account.tax', 'Retenció a aplicar', required=True,
            help='Retenció IRPF a aplicar', domain=[('name','like','IRPF')]
        ),
        'info': fields.text('Info')
    }

    _defaults = {
        'info': _default_info,
    }

WizardComputeMod193Invoice()
