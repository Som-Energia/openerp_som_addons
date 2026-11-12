from ..component_utils import dateformat
from ..ProcesR1 import ProcesR1


class R102(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "R102"
        result["rebuig"] = step.rebuig
        result["motiu_rebuig"] = step.motiu_rebuig
        result["codi_reclamacio_distri"] = step.codi_reclamacio_distri
        result["data_acceptacio"] = dateformat(step.data_acceptacio)
        result["data_rebuig"] = dateformat(step.data_rebuig)
        return result
