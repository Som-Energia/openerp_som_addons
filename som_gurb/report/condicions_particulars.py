import pooler
import netsvc
from report.interface import report_int


class ConditionsGurbReport(report_int):

    def create(self, cursor, uid, ids, datas, context=None):
        if context is None:
            context = {}

        pool = pooler.get_pool(cursor.dbname)
        gurb_cups_o = pool.get("som.gurb.cups")

        for gurb_cups_id in ids:
            pol_id = gurb_cups_o.get_polissa_gurb_cups(
                cursor, uid, gurb_cups_id, context=context
            )

            report = netsvc.LocalService('report.giscedata.polissa')

            return report.create(cursor, uid, [pol_id], {}, context=context)


ConditionsGurbReport('report.som.gurb.conditions')
