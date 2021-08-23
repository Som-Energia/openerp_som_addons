from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesA3 import ProcesA3

class A301(ProcesA3.ProcesA3):
    def __init__(self):
        ProcesA3.ProcesA3.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesA3.ProcesA3.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'A301'
        result['text'] = step.comentaris
        result['tipus_contracte'] =  get_description(step.tipus_contracte, "TABLA_9")
        result['tarifa'] =  get_description(step.tarifaATR, "TABLA_17")
        result['potencies'] = []
        for pot in step.pot_ids:
            if pot.potencia != 0:
                result['potencies'].append({
                        'name' : pot.name,
                        'potencia' : pot.potencia
                    })
        result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]

        swl_obj = step.pool.get('giscedata.switching.log')

        search_params = [
            ('request_code','=',step.sw_id.codi_sollicitud),
            ('tipus','=','export'),
            ('proces','=','A3'),
            ('pas','=', '01'),
            ('status', '=', 'correcte')
        ]
        swl_ids = swl_obj.search(cursor, uid, search_params)

        if len(swl_ids) > 0:
            swl = swl_obj.browse(cursor, uid, swl_ids[0])
            result['day'] = dateformat(swl.case_date)

        return result