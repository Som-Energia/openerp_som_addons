from report_puppeteer.report_puppeteer import PuppeteerParser
from .report_backend_ccpp import ReportBackendCondicionsParticulars


class ReportBackendCondicionsParticularsIgnoreModcon(ReportBackendCondicionsParticulars):
    """Is the same report, but ignores modcons"""
    _name = "report.backend.condicions.particulars.ignore.modcon"

    def get_polissa_data(self, cursor, uid, pol, context=None):
        context = context or {}
        context.update({'ignore_modcon_pricelist': True})
        res = super(ReportBackendCondicionsParticularsIgnoreModcon, self).get_polissa_data(
            cursor, uid, pol, context=context)
        return res


ReportBackendCondicionsParticularsIgnoreModcon()


PuppeteerParser(
    'report.somenergia.polissa_ignore_modcon',
    'report.backend.condicions.particulars.ignore.modcon',
    'som_polissa_condicions_generals/report/condicions_particulars_puppeteer.mako',
    params={}
)
