from ..component_utils import dateformat, get_description
from ..ProcesB2 import ProcesB2


class B205(ProcesB2.ProcesB2):
    def __init__(self):
        ProcesB2.ProcesB2.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesB2.ProcesB2.get_data(self, wiz, cursor, uid, step)
        result["type"] = "B205"
        result["data_activacio"] = dateformat(step.data_activacio)
        result["motiu_baixa"] = get_description(step.motiu, "TABLA_120")
        return result
