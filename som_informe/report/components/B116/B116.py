from ..component_utils import get_description
from ..ProcesB1 import ProcesB1


class B116(ProcesB1.ProcesB1):
    def __init__(self):
        ProcesB1.ProcesB1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesB1.ProcesB1.get_data(self, wiz, cursor, uid, step)
        result["type"] = "B116"
        result["contestacio_incidencia"] = get_description(step.contestacio, "TABLA_121")
        result["nom_contacte"] = step.nom_contacte
        result["email_contacte"] = step.email
        result["telefons"] = [{"numero": telefon.numero} for telefon in step.telefons]
        return result
