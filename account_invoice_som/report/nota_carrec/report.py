from __future__ import absolute_import

from report_puppeteer.report_puppeteer import PuppeteerParser

PuppeteerParser(
    'report.nota.carrec',
    'report.backend.account.invoice.nota.carrec',
    'account_invoice_som/report/nota_carrec/index.mako',
    params={}
)