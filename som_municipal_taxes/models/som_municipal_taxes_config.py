# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from autoworker import AutoWorker
from oorq.decorators import job, create_jobs_group
from base_extended.base_extended import NoDependency
from giscedata_municipal_taxes.taxes.municipal_taxes_invoicing import MunicipalTaxesInvoicingReport

ANUAL_VAL = 5


class SomMunicipalTaxesConfig(osv.osv):
    _name = 'som.municipal.taxes.config'

    def on_change_parnter_get_bank(self, cr, uid, ids, partner_id, context=None):
        partner_obj = self.pool.get('res.partner')
        bank_id = partner_obj.get_default_bank(cr, uid, partner_id)
        return {'value': {'bank_id': bank_id}}

    _columns = {
        'name': fields.char("Nom", size=128),
        'municipi_id': fields.many2one('res.municipi', 'Municipi', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'bank_id': fields.many2one('res.partner.bank', 'Compte bancari'),
        'payment_order': fields.boolean('Remesa', help="Marcar si es vol crear \
                                        remesa de pagament"),
        'red_sara': fields.boolean('Red SARA', help="Marcar si es demanar carta de  \
                                   pagament al Registre General"),
        'active': fields.boolean('Active'),
        'payment': fields.selection([("quarter", "Trimestral"), ("year", "Anual")],
                                    "Periode de pagament"),
    }

    def generate_municipal_taxes_file_path(self, cr, uid, ids, municipi_id, context=None):
        start_date, end_date = self.get_dates_from_quarter(context['any'], context['trimestre'])
        polissa_categ_imu_ex_id = (
            self.pool.get('ir.model.data').get_object_reference(
                cr, uid, 'giscedata_municipal_taxes', 'contract_categ_imu_ex'
            )[1]
        )
        invoiced_states = self.pool.get(
            'giscedata.facturacio.extra').get_states_invoiced(cr, uid)
        taxes_invoicing_report = MunicipalTaxesInvoicingReport(
            cr, uid, start_date, end_date, False, "xlsx", False,
            polissa_categ_imu_ex_id, False, invoiced_states,
            context=context
        )
        totals = taxes_invoicing_report.get_totals_by_city([municipi_id])
        if not totals:
            return False

        output_binary = taxes_invoicing_report.build_report_taxes([municipi_id])
        path = "/tmp/municipal_taxes_{}.xlsx".format(municipi_id)
        with open(path, 'wb') as file:
            file.write(output_binary)
        return path

    def encuar_crawlers(self, cr, uid, ids, municipis_conf_ids, context=None):
        mun_obj = self.pool.get('res.municipi')
        crawler_id = self.pool.get('ir.model.data').get_object_reference(
            cr, uid, 'som_crawlers', 'carregar_registre_general',
        )[1]
        jobs_ids = []
        with NoDependency():
            for municipi_conf_id in municipis_conf_ids:
                municipi_id = self.read(cr, uid, municipi_conf_id, [
                                        'municipi_id'])['municipi_id'][0]
                context['codi_municipi'] = mun_obj.read(
                    cr, uid, municipi_id, ['codi_dir3'])['codi_dir3']
                context['file_path'] = self.generate_municipal_taxes_file_path(
                    cr, uid, ids, municipi_id, context)
                if context['file_path']:
                    j = self.crawler_redsaras_async(
                        cr, uid, crawler_id, municipi_conf_id, context
                    )
                    jobs_ids.append(j.id)
                else:
                    print("No hi ha factures al municipi {}".format(context['codi_municipi']))

        create_jobs_group(
            cr.dbname, uid, 'Crawlers Red Saras: {} municipis'.format(
                len(municipis_conf_ids)
            ), 'crawler_redsaras', jobs_ids
        )
        aw = AutoWorker(queue='crawler_redsaras', default_result_ttl=24 * 3600, max_procs=1)
        aw.work()

    @job(queue='crawler_redsaras')
    def crawler_redsaras_async(self, cursor, uid, id, municipi_id, context=None):
        return self.crawler_redsaras(cursor, uid, id, context=context)

    def crawler_redsaras(self, cursor, uid, id, context=None):
        task_obj = self.pool.get("som.crawlers.task")
        task_obj.executar_tasca(cursor, uid, id, context)

    def get_dates_from_quarter(self, year, quarter):
        if quarter == ANUAL_VAL:
            return date(year, 1, 1), date(year, 12, 31)
        else:
            start_date = date(year, (quarter - 1) * 3 + 1, day=1)
            return (
                start_date,
                start_date + relativedelta(months=3) - timedelta(days=1)
            )


SomMunicipalTaxesConfig()
