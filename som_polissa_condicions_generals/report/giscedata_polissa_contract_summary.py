# -*- coding: utf-8 -*-
from report_puppeteer.report_puppeteer import PuppeteerParser


PuppeteerParser(
    "report.giscedata.polissa.contract.summary",
    "report.backend.contract.summary",
    "som_polissa_condicions_generals/report/contract_summary_puppeteer.mako",
    params={}
)
