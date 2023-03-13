from ..component_utils import dateformat, get_description
from ..ProcesB1 import ProcesB1


class B101(ProcesB1.ProcesB1):
    def __init__(self):
        ProcesB1.ProcesB1.__init__(self)

    def step_name(self):
        return "01"

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesB1.ProcesB1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "B101"
        result["text"] = step.comentaris
        result["motiu_baixa"] = get_description(step.motiu, "TABLA_10")
        start_date = self.get_log_date(wiz, cursor, uid, step)
        if start_date:
            result["day"] = dateformat(start_date)
            result["date"] = start_date

        return result
