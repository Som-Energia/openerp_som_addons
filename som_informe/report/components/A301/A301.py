from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesA3 import ProcesA3

class A301(ProcesA3.ProcesA3):
    def __init__(self):
        ProcesA3.ProcesA3.__init__(self)

    def step_name(self):
        return '01'

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesA3.ProcesA3.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'A301'
        result['text'] = step.comentaris
        result['tipus_contracte'] =  get_description(step.tipus_contracte, "TABLA_9")
        result['tarifa'] =  get_description(step.tarifaATR, "TABLA_17")
        result['potencies'] = [{'name':pot.name, 'potencia':pot.potencia} for pot in step.pot_ids if pot.potencia != 0]
        result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]
        result['day'] = self.get_log_date(wiz, cursor, uid, step)
        return result