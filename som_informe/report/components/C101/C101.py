from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesC1 import ProcesC1

class C101(ProcesC1.ProcesC1):
    def __init__(self):
        ProcesC1.ProcesC1.__init__(self)

    def step_name(self):
        return '01'

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC1.ProcesC1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'C101'
        result['text'] = step.comentaris
        if len(step.document_ids) == 0:
            result['adjunts'] = False
        result['day'] = self.get_log_date(wiz, cursor, uid, step)

        return result