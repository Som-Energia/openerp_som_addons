from ..component_utils import dateformat
from ..ProcesATR import ProcesATR

class ProcesC1(ProcesATR.ProcesATR):

    def __init__(self):
        ProcesATR.ProcesATR.__init__(self)

    def proces_name(self):
        return 'C1'

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesATR.ProcesATR.get_data(self, wiz, cursor, uid, step)
        result['date'] = step.date_created
        result['day'] = dateformat(step.date_created)
        result['create'] = dateformat(step.date_created, True)
        result['pas'] = step.sw_id.step_id.name
        result['codi_solicitud'] = step.sw_id.codi_sollicitud
        result['titol'] = step.sw_id.proces_id.name + " - " + step.sw_id.step_id.name
        result['distribuidora'] = step.sw_id.partner_id.name
        return result