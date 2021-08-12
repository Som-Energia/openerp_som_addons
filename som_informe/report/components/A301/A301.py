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
            result['potencies'].append({
                    'name' : pot.name,
                    'potencia' : pot.potencia
                })
        result['documents_adjunts'] = [(get_description(doc.type, "TABLA_61"), doc.url) for doc in step.document_ids]
        import pudb; pu.db
        swl_obj = step.pool.get('giscedata.switching.log')

        proces = step.sw_id.codi_sollicitud[:len(step.sw_id.codi_sollicitud)//2]
        pas = step.sw_id.codi_sollicitud[len(step.sw_id.codi_sollicitud)//2:]

        #swl_ids = swl_obj.search(cursor, uid,[('request_code','=',step.sw_id.codi_sollicitud),('tipus','=','export'),('sw_proces','=',proces), ('sw_pas','=',pas)])
        swl_ids = swl_obj.search(cursor, uid,[('request_code','=',step.sw_id.codi_sollicitud)])

        if swl_ids != []:
            swl_obj.browse(swl_ids[0])
            result['date'] = swl_obj.data
            result['day'] = dateformat(swl_obj.data)

        return result