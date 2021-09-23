from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesE1 import ProcesE1

class E108(ProcesE1.ProcesE1):
    def __init__(self):
        ProcesE1.ProcesE1.__init__(self)

    def step_name(self):
        return '08'

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesE1.ProcesE1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'E108'
        result['day'] = self.get_log_date(wiz, cursor, uid, step)
        return result
