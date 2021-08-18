from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesB1 import ProcesB1

class B103(ProcesB1.ProcesB1):
    def __init__(self):
        ProcesB1.ProcesB1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesB1.ProcesB1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'B103'

        
        swl_obj = step.pool.get('giscedata.switching.log')

        search_params = [
            ('request_code','=',step.sw_id.codi_sollicitud),
            ('tipus','=','export'),
            ('proces','=','B1'),
            ('pas','=', '03'),
            ('status', '=', 'correcte')
        ]
        swl_ids = swl_obj.search(cursor, uid, search_params)

        if len(swl_ids) > 0:
            swl = swl_obj.browse(cursor, uid, swl_ids[0])
            result['day'] = dateformat(swl.case_date)
        

        return result
