from report_backend.report_backend import ReportBackend, report_browsify
from report_puppeteer.report_puppeteer import PuppeteerParser


class ReportBackendCondicionsParticularsM1(ReportBackend):
    _source_model = "giscedata.switching"
    _name = "report.backend.condicions.particulars.m1"

    def get_lang(self, cursor, uid, record_id, context=None):
        if context is None:
            context = {}

        sw_obj = self.pool.get('giscedata.switching')
        sw = sw_obj.browse(cursor, uid, record_id, context)
        lang = sw.cups_polissa_id.titular.lang
        return lang

    @report_browsify
    def get_data(self, cursor, uid, sw, context=None):
        if context is None:
            context = {}

        pol_id = sw.cups_polissa_id.id
        context.update({"m1_id": sw.id})
        return self.pool.get("report.backend.condicions.particulars").get_data(cursor, uid, pol_id, context=context)  # noqa: E501


ReportBackendCondicionsParticularsM1()


PuppeteerParser(
    'report.somenergia.polissa_m101',
    'report.backend.condicions.particulars.m1',
    'som_polissa_condicions_generals/report/condicions_particulars_puppeteer.mako',
    params={}
)
