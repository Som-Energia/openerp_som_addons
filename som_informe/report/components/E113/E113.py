from ..component_utils import get_description
from ..ProcesE1 import ProcesE1


class E113(ProcesE1.ProcesE1):
    def __init__(self):
        ProcesE1.ProcesE1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesE1.ProcesE1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "E113"
        result["contestacio_incidencia"] = get_description(step.tipus_contestacio, "TABLA_121")
        result["nom_contacte"] = step.nom_contacte
        result["email_contacte"] = step.email
        result["telefons"] = [{"numero": telefon.numero} for telefon in step.telefons]
        return result
