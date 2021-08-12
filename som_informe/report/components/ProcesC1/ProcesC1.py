from ..component_utils import dateformat

class ProcesC1:

    def __init__(self):
        pass

    def get_data(self, wiz, cursor, uid, step):
        result = {}
        result['date'] = step.date_created
        result['day'] = dateformat(step.date_created)
        result['create'] = dateformat(step.date_created, True)
        result['pas'] = step.sw_id.step_id.name
        result['codi_solicitud'] = step.sw_id.codi_sollicitud
        result['titol'] = step.sw_id.proces_id.name + " - " + step.sw_id.step_id.name
        result['distribuidora'] = step.sw_id.partner_id.name
        return result