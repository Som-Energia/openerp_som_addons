from ..component_utils import dateformat, get_description
from ..ProcesE1 import ProcesE1


class E101(ProcesE1.ProcesE1):
    def __init__(self):
        ProcesE1.ProcesE1.__init__(self)

    def step_name(self):
        return "01"

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesE1.ProcesE1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "E101"
        result["tipus_solicitud"] = get_description(step.tipus_sollicitud, "TABLA_122")
        result["codi_subjacent"] = step.atr_subjacent.codi_sollicitud
        result["data_subjacent"] = dateformat(step.atr_subjacent.data_sollicitud)
        start_date = self.get_log_date(wiz, cursor, uid, step)
        if start_date:
            result["day"] = dateformat(start_date)
            result["date"] = start_date
        return result
