from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesE1 import ProcesE1

class E103(ProcesE1.ProcesE1):
    def __init__(self):
        ProcesE1.ProcesE1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesE1.ProcesE1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'E103'
        result['data_creacio'] = step.date_created
        result['data_incidencia'] = step.data_incidencia
        result['data_prevista_accio'] = step.data_prevista_accio
        result['incidencies'] = []
        for incidencia in step.incidencia_ids:
            result['incidencies'].append({
                    'tipus' : incidencia.motiu_incidencia,
                    'comentari' : incidencia.desc_incidencia
            })
        return result
