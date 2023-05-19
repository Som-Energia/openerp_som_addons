from ..component_utils import dateformat
from ..ProcesC2 import ProcesC2


class C212(ProcesC2.ProcesC2):
    def __init__(self):
        ProcesC2.ProcesC2.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC2.ProcesC2.get_data(self, wiz, cursor, uid, step)
        result["type"] = "C212"
        result["data_rebuig"] = dateformat(step.data_rebuig)

        return result
