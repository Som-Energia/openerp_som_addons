from ..component_utils import dateformat
from ..ProcesB1 import ProcesB1


class B102(ProcesB1.ProcesB1):
    def __init__(self):
        ProcesB1.ProcesB1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesB1.ProcesB1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "B102"
        result["rebuig"] = step.rebuig
        result["rebutjos"] = [
            {"codi": rebuig.motiu_rebuig.name, "descripcio": rebuig.desc_rebuig}
            for rebuig in step.rebuig_ids
        ]
        result["data_rebuig"] = dateformat(step.data_rebuig)
        result["data_activacio"] = dateformat(step.data_ult_lect)
        return result
