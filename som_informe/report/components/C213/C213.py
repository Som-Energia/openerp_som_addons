from gestionatr.utils import get_description
from ..ProcesC2 import ProcesC2

class C213(ProcesC2.ProcesC2):
    def __init__(self):
        ProcesC2.ProcesC2.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC2.ProcesC2.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'C213'
        result['data_creacio'] = step.date_created
        result['contestacio_incidencia'] = get_description(step.tipus_contestacio, "TABLA_121")
        result['nom_contacte'] = step.nom_contacte
        result['email_contacte'] = step.email
        result['telefons'] = []
        for telefon in step.telefons:
            result['telefons'].append({
                'numero' : telefon.numero
            })


        return result
