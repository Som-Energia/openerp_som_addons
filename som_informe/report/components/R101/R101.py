from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesR1 import ProcesR1

class R101(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'R101'
        result['tipus_reclamacio'] = step.subtipus_id.name + " - " + step.subtipus_id.desc if step.subtipus_id else ''
        result['text'] = step.comentaris
        result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]
        result['variables_aportacio'] = []
        for var_apo in step.vars_aportacio_info_ids:
            result['variables_aportacio'].append({
                    'valor': var_apo.valor,
                    'variable': get_description(var_apo.variable, "TABLA_76"),
                    'descripcio': var_apo.desc_peticio_info,
                    'tipus': get_description(var_apo.tipus_info, "TABLA_85"),
                })
        return result