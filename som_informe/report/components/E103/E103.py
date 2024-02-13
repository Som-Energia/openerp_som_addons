from ..component_utils import dateformat
from ..ProcesE1 import ProcesE1


class E103(ProcesE1.ProcesE1):
    def __init__(self):
        ProcesE1.ProcesE1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesE1.ProcesE1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "E103"
        result["data_incidencia"] = dateformat(step.data_incidencia)
        result["data_prevista_accio"] = dateformat(step.data_prevista_accio)
        result["incidencies"] = [
            {"tipus": incidencia.motiu_incidencia, "comentari": incidencia.desc_incidencia}
            for incidencia in step.incidencia_ids
        ]
        return result
