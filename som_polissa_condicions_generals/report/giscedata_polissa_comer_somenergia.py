# -*- coding: utf-8 -*-
from report_puppeteer.report_puppeteer import PuppeteerParser


PuppeteerParser(
    "report.giscedata.polissa",
    "report.backend.condicions.particulars",
    "som_polissa_condicions_generals/report/condicions_particulars_puppeteer.mako",
    params={}
)
