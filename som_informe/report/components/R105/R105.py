from gestionatr.utils import get_description
from ..ProcesR1 import ProcesR1

class R105(ProcesR1.ProcesR1):
    def __init__(self):
        ProcesR1.ProcesR1.__init__(self)

    def get_data(self, cursor, uid, step):
        result = ProcesR1.ProcesR1.get_data(self, cursor, uid, step)
        result['type'] = 'R105'
        result['codi_reclamacio_distri'] = step.codi_reclamacio_distri
        result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]
        result['comentaris_distri'] = step.comentaris
        result['resultat'] = get_description(step.resultat, 'TABLA_80')
        detail_obj = self.pool.get('giscedata.switching.detalle.resultado')
        ids = detail_obj.search(cursor, uid, [])
        vals = detail_obj.read(cursor, uid, ids, ['name', 'text'])
        details = dict([(v['name'], v['text']) for v in vals])
        result['detall_resultat'] = details.get(step.detall_resultat, step.detall_resultat)
        return result