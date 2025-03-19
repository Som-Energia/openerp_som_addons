from ..component_utils import dateformat
from ..ProcesM1 import ProcesM1


class M103(ProcesM1.ProcesM1):
    def __init__(self):
        ProcesM1.ProcesM1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesM1.ProcesM1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "M103"
        result["data_incidencia"] = dateformat(step.data_incidencia)
        result["data_prevista_accio"] = dateformat(step.data_prevista_accio)
        result["incidencies"] = [
            {"tipus": incidencia.motiu_incidencia, "comentari": incidencia.desc_incidencia}
            for incidencia in step.incidencia_ids
        ]
        return result
