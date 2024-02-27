from ..component_utils import dateformat
from ..ProcesB1 import ProcesB1


class B106(ProcesB1.ProcesB1):
    def __init__(self):
        ProcesB1.ProcesB1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesB1.ProcesB1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "B106"
        result["data_incidencia"] = dateformat(step.data_incidencia)
        result["data_prevista_accio"] = dateformat(step.data_prevista_accio)
        result["incidencies"] = [
            {"tipus": incidencia.motiu_incidencia, "comentari": incidencia.desc_incidencia}
            for incidencia in step.incidencia_ids
        ]
        return result
