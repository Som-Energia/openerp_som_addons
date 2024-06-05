from report_backend.report_backend import ReportBackend, report_browsify
from report_puppeteer.report_puppeteer import PuppeteerParser


class ReportBackendCondicionsParticularsM1(ReportBackend):
    _source_model = "giscedata.switching"
    _name = "report.backend.condicions.particulars.m1"

    @report_browsify
    def get_data(self, cursor, uid, sw, context=None):
        bcknd_obj = self.pool.get('report.backend.condicions.particulars')
        pol_id = sw.polissa_id
        context.update({"m1_id": sw.id})
        return bcknd_obj.get_data(pol_id, context)


ReportBackendCondicionsParticularsM1()


PuppeteerParser(
    'report.report_condicions_particulars_m1',
    'report.backend.condicions.particulars.m1',
    'som_polissa_condicions_generals/report/condicions_particulars_puppeteer.mako',
    params={}
)
