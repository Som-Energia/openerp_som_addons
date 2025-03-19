from ..component_utils import get_description
from ..ProcesM1 import ProcesM1


class M113(ProcesM1.ProcesM1):
    def __init__(self):
        ProcesM1.ProcesM1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesM1.ProcesM1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "M113"
        result["contestacio_incidencia"] = get_description(step.tipus_contestacio, "TABLA_121")
        result["nom_contacte"] = step.nom_contacte
        result["email_contacte"] = step.email
        result["telefons"] = [{"numero": telefon.numero} for telefon in step.telefons]
        return result
