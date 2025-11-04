# -*- encoding: utf-8 -*-
from osv import osv, fields
from tools import config
from tools.translate import _


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
              u"Generation kWh de l'any {name} ({start} -> {end})"

        dates = self.get_year(cursor, uid, context)

        res = txt.format(**dates)

        return res

    def do_action(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz_id = ids[0]
        wiz = self.browse(cursor, uid, wiz_id, context)

        report_obj = self.pool.get('l10n.es.aeat.mod193.report')
        record_obj = self.pool.get('l10n.es.aeat.mod193.record')
        partner_obj = self.pool.get('res.partner')
        part_add_obj = self.pool.get('res.partner.address')
        report_id = context.get('active_id')

        report = report_obj.browse(cursor, uid, report_id, context)

        dates = self.get_year(cursor, uid, context)

        txt = u"Calculant linies del model 193 de la AEAT " \
              u"per l'any fiscal {name}\n" \
              u"Buscarem les factures entre les dates " \
              u"{start} i {end}".format(**dates)

        common_vals = {
            'report_id': report.id,
            'lr_vat': '',
            'mediator': False,
            'code_key': '1',
            'code_value': report.company_vat,
            'incoming_key': 'B',
            'nature': '03',
            'payment': '1',
            'code_type': False,
            'code_bank': '',
            'pending': ' ',
            'fiscal_year_id': report.fiscalyear_id.id,
            'incoming_type': '2'
        }

        query_file = (u"%s/som_generationkwh/sql/aeat193_from_gkwh_invoices_query.sql" % config['addons_path'])
        with open(query_file) as f:
            query = f.read()
        cursor.execute(query, dict(start=dates['start'], end=dates['end']))

        new_linies = 0
        for data in cursor.fetchall():
            partner_id = data[0]
            partner_vat = data[1]
            amount = float(data[2])

            part_add_id = part_add_obj.search(cursor, uid, [('partner_id', '=', partner_id)])
            if not part_add_id:
                raise osv.except_osv("Error",
                                     _(u"No s'han trobat adreces pel partner amb VAT {} i ID {}").
                                     format(partner_vat, partner_id))

            state_id = part_add_obj.read(cursor, uid, part_add_id[0], ['state_id'])
            if not state_id:
                raise osv.except_osv("Error",
                                     _(u"L'adreça amb ID {} pel partner amb VAT {} no té definida província. "
                                       u"Aquesta és necessària pel procés. Si us plau revisi les dades.").
                                     format(part_add_id, partner_vat))

            partner_nif = partner_vat.replace('ES', '')
            vals = common_vals.copy()
            vals.update({
                'partner_id': partner_id,
                'partner_vat': partner_nif,
                'amount': amount,
                'amount_base': amount,
                'amount_tax': amount * abs(wiz.tax_id.amount),
                'tax_percent': wiz.tax_id.amount * 100,
                'state_id': state_id['state_id'][0],
                'postal_address_id': part_add_id[0],
                'fiscal_address_id': part_add_id[0]
            })

            record_obj.create(cursor, uid, vals)
            new_linies += 1

        txt += u'\nAfegides {} línies al model 193.'.format(new_linies)

        wiz.write({'info': txt, 'state': 'done'})

    _columns = {
        'tax_id': fields.many2one(
            'account.tax', 'Retenció a aplicar', required=True,
            help='Retenció IRPF a aplicar', domain=[('name', 'like', 'IRPF')]
        ),
        'info': fields.text('Info'),
        'state': fields.char('State', size=16),
    }

    _defaults = {
        'info': _default_info,
        'state': lambda *a: 'init',
    }


WizardComputeMod193Invoice()
