from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesA3 import ProcesA3

class A302(ProcesA3.ProcesA3):
    def __init__(self):
        ProcesA3.ProcesA3.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesA3.ProcesA3.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'A302'
        result['rebuig'] = step.rebuig
        #result['codiRebuig'] = ''
        #if step.rebuig == 'Rebuig':
        #result['descipcioRebuig'] = step.motiu_rebuig
        #result['dataRebuig'] = step.data_rebuig
        result['rebutjos'] = []
        for rebuig in step.rebuig_ids:
            result['rebutjos'].append({
                    'codi' : rebuig.motiu_rebuig.name,
                    'descripcio' : rebuig.desc_rebuig
                })
        result['data_rebuig'] = step.data_rebuig
        #result['text'] = step.comentaris
        #result['tipus_contracte'] =  get_description(step.tipus_contracte, "TABLA_9")
        #result['tarifa'] =  get_description(step.tarifaATR, "TABLA_17")
        '''result['potencies'] = []
        for pot in step.pot_ids:
            result['potencies'].append({
                    'name' : pot.name,
                    'potencia' : pot.potencia
                })
        result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]
        '''

        return result
