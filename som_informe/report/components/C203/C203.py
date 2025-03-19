from ..component_utils import dateformat
from ..ProcesC2 import ProcesC2


class C203(ProcesC2.ProcesC2):
    def __init__(self):
        ProcesC2.ProcesC2.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC2.ProcesC2.get_data(self, wiz, cursor, uid, step)
        result["type"] = "C203"
        result["data_incidencia"] = dateformat(step.data_incidencia)
        result["data_prevista_accio"] = dateformat(step.data_prevista_accio)
        result["incidencies"] = [
            {"tipus": incidencia.motiu_incidencia, "comentari": incidencia.desc_incidencia}
            for incidencia in step.incidencia_ids
        ]
        return result
