from gestionatr.utils import get_description
from ..ProcesR1 import ProcesR1

class R104(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, cursor, uid, step)
        result['type'] = 'R104'
        result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]
        result['comentaris_distri'] = step.comentaris
        result['hi_ha_client'] = step.hi_ha_client
        result['hi_ha_var_info'] = step.hi_ha_var_info
        result['hi_ha_var_info_retip'] = step.hi_ha_var_info_retip
        return result