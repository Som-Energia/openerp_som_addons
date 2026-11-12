from ..component_utils import dateformat
from ..ProcesE1 import ProcesE1


class E110(ProcesE1.ProcesE1):
    def __init__(self):
        ProcesE1.ProcesE1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesE1.ProcesE1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "E110"
        result["data_acceptacio"] = dateformat(step.data_acceptacio)

        return result
