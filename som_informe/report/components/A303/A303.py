from ..component_utils import dateformat
from ..ProcesA3 import ProcesA3


class A303(ProcesA3.ProcesA3):
    def __init__(self):
        ProcesA3.ProcesA3.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesA3.ProcesA3.get_data(self, wiz, cursor, uid, step)
        result["type"] = "A303"
        result["data_incidencia"] = dateformat(step.data_incidencia)
        result["data_prevista_accio"] = dateformat(step.data_prevista_accio)
        result["incidencies"] = [
            {"tipus": incidencia.motiu_incidencia, "comentari": incidencia.desc_incidencia}
            for incidencia in step.incidencia_ids
        ]
        return result
