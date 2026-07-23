from report_backend.report_backend import ReportBackend, report_browsify
from report_puppeteer.report_puppeteer import PuppeteerParser


class ReportBackendCondicionsParticularsIgnoreModcon(ReportBackend):
    """Is the same report, but ignores modcons"""
    _name = "report.backend.condicions.particulars.ignore.modcon"

    @report_browsify
    def get_data(self, cursor, uid, pol, context=None):
        context = context or {}
        context.update({'ignore_modcon_pricelist': True})

        return self.pool.get(
            'report.backend.condicions.particulars'
        ).get_data(cursor, uid, pol, context=context)

    def get_polissa_data(self, cursor, uid, pol, context=None):
        context = context or {}
        context.update({'ignore_modcon_pricelist': True})
        return self.pool.get(
            'report.backend.condicions.particulars'
        ).get_polissa_data(cursor, uid, pol, context=context)

    def get_prices_data(self, cursor, uid, pol, context=None):
        context = context or {}
        context.update({'ignore_modcon_pricelist': True})
        return self.pool.get(
            'report.backend.condicions.particulars'
        ).get_prices_data(cursor, uid, pol, context=context)


ReportBackendCondicionsParticularsIgnoreModcon()


PuppeteerParser(
    'report.somenergia.polissa_ignore_modcon',
    'report.backend.condicions.particulars.ignore.modcon',
    'som_polissa_condicions_generals/report/condicions_particulars_puppeteer.mako',
    params={}
)
