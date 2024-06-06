from __future__ import absolute_import
from report_puppeteer.report_puppeteer import PuppeteerParser

PuppeteerParser(
    'report.giscedata.facturacio.resum.deute',
    'report.resum.deute.backend',
    'giscedata_facturacio_som/report/resum_factures_deute.mako',
    params={}
)
