from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesA3 import ProcesA3

class A303(ProcesA3.ProcesA3):
    def __init__(self):
        ProcesA3.ProcesA3.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesA3.ProcesA3.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'A303'
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
