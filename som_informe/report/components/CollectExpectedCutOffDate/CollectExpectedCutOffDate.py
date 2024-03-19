from datetime import timedelta
from ..component_utils import to_date, to_string, has_category

ESTAT_PENDENT_INPAGAT_MIN = 33
ANNEX_4_IDS = [41, 65]
ANNEX_2_IDS = [45]


class CollectExpectedCutOffDate:
    def __init__(self):
        pass

    def get_data(self, cursor, uid, wiz, context):
        if has_category(wiz.polissa, [11, 27]):
            return {"type": "Empty"}

        fact_obj = wiz.pool.get("giscedata.facturacio.factura")
        search_parameters = [
            ("polissa_id", "=", wiz.polissa.id),
            ("type", "=", "out_invoice"),
            ("residual", ">", 0),
            ("pending_state", ">", ESTAT_PENDENT_INPAGAT_MIN),
        ]
        fact_ids = fact_obj.search(cursor, uid, search_parameters, limit=1, order="date_invoice")

        if not fact_ids:
            return {"type": "Empty"}

        data_annex_4 = None
        data_annex_2 = None
        fact = fact_obj.browse(cursor, uid, fact_ids[0])
        for ph in fact.pending_history_ids:
            if ph.pending_state_id.id in ANNEX_4_IDS:
                data_annex_4 = ph.change_date
            if ph.pending_state_id.id in ANNEX_2_IDS:
                data_annex_2 = ph.change_date

        cut_off_date = "ERROR data no trobada!!"
        if data_annex_4:
            cut_off_date = to_string(to_date(data_annex_4) + timedelta(days=20))
        elif data_annex_2:
            cut_off_date = to_string(to_date(data_annex_2) + timedelta(days=60))

        return {
            "type": "CollectExpectedCutOffDate",
            "expected_cut_off_date": cut_off_date,
            "distri_name": wiz.polissa.distribuidora.name,
        }
