from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesE1 import ProcesE1

class E111(ProcesE1.ProcesE1):
    def __init__(self):
        ProcesE1.ProcesE1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesE1.ProcesE1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'E111'
        result['data_alta'] = dateformat(step.data_activacio)
        return result
