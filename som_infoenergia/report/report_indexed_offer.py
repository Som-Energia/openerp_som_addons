# -*- coding: utf-8 -*-

from c2c_webkit_report import webkit_report
from report import report_sxw
from tools import config
from osv import osv
from yamlns import namespace as ns


class report_webkit_html(report_sxw.rml_parse):
    def __init__(self, cursor, uid, name, context):
        super(report_webkit_html, self).__init__(cursor, uid, name, context=context)
        self.localcontext.update(
            {
                "cursor": cursor,
                "uid": uid,
                "addons_path": config["addons_path"],
            }
        )


webkit_report.WebKitParser(
    "report.som.enviament.massiu",
    "som.enviament.massiu",
    "som_infoenergia/report/report_indexed_offer.mako",
    parser=report_webkit_html,
)


class OnDemandDataGenerator:
    def __init__(self, cursor, uid, object, extra_text, context):
        self.cursor = cursor
        self.uid = uid
        self.object = object
        self.extra_text = extra_text
        self.context = context
        self.cache = {}

    def factory_data_extractor(self, component_name):
        exec (
            "from components."
            + component_name
            + " import "
            + component_name
            + ";extractor = "
            + component_name
            + "."
            + component_name
            + "()"
        )
        return extractor

    def __getattr__(self, name):
        if name not in self.cache.keys():
            extractor = self.factory_data_extractor(name)
            data = extractor.get_data(
                self.cursor, self.uid, self.object, self.extra_text, self.context
            )
            self.cache[name] = ns.loads(ns(data).dump())

        return self.cache[name]


class ReportIndexedOffer(osv.osv_memory):
    _name = "report.indexed.offer"

    def get_report_data(self, cursor, uid, objects, context=None):
        datas = []
        for object in objects:
            if object.extra_text:
                extra_text = eval(object.extra_text)
                for k in extra_text.keys():
                    if k.strip() not in extra_text:
                        extra_text[k.strip()] = extra_text[k]
            else:
                extra_text = {}
            datas.append(OnDemandDataGenerator(cursor, uid, object, extra_text, context))
        return datas

    _columns = {}
    _defaults = {}


ReportIndexedOffer()
