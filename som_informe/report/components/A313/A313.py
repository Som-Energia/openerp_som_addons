from ..component_utils import dateformat
from gestionatr.utils import get_description
from ..ProcesA3 import ProcesA3

class A313(ProcesA3.ProcesA3):
    def __init__(self):
        ProcesA3.ProcesA3.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesA3.ProcesA3.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'A313'
        result['data_creacio'] = dateformat(step.date_created)
        result['contestacio_incidencia'] = get_description(step.tipus_contestacio, "TABLA_121")
        result['nom_contacte'] = step.nom_contacte
        result['email_contacte'] = step.email
        result['telefons'] = []
        for telefon in step.telefons:
            result['telefons'].append({
                'numero' : telefon.numero
            })


        return result
