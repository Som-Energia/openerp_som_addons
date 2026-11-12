from ..component_utils import dateformat
from ..ProcesB1 import ProcesB1


class B105(ProcesB1.ProcesB1):
    def __init__(self):
        ProcesB1.ProcesB1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesB1.ProcesB1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "B105"
        result["data_activacio"] = dateformat(step.data_activacio)
        return result
