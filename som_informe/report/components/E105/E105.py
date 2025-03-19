from ..component_utils import dateformat, get_description
from ..ProcesE1 import ProcesE1


class E105(ProcesE1.ProcesE1):
    def __init__(self):
        ProcesE1.ProcesE1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesE1.ProcesE1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "E105"
        result["data_activacio"] = dateformat(step.data_activacio)
        result["resultat_activacio"] = get_description(step.resultat_activacio, "TABLA_118")
        return result
