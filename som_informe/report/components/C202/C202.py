from ..component_utils import dateformat
from ..ProcesC2 import ProcesC2


class C202(ProcesC2.ProcesC2):
    def __init__(self):
        ProcesC2.ProcesC2.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC2.ProcesC2.get_data(self, wiz, cursor, uid, step)
        result["type"] = "C202"
        result["rebuig"] = step.rebuig
        result["rebutjos"] = [
            {"codi": rebuig.motiu_rebuig.name, "descripcio": rebuig.desc_rebuig}
            for rebuig in step.rebuig_ids
        ]
        result["data_rebuig"] = dateformat(step.data_rebuig)
        return result
