from gestionatr.utils import get_description
from ..ProcesD1 import ProcesD1
from ..component_utils import dateformat

class D102(ProcesD1.ProcesD1):
    def __init__(self):
        ProcesD1.ProcesD1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesD1.ProcesD1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'D102'
        result['rebuig'] = step.rebuig
        result['rebutjos'] = []
        for rebuig in step.rebuig_ids:
            result['rebutjos'].append({
                    'codi' : rebuig.motiu_rebuig.name,
                    'descripcio' : rebuig.desc_rebuig
                })

        
        swl_obj = step.pool.get('giscedata.switching.log')

        search_params = [
            ('request_code','=',step.sw_id.codi_sollicitud),
            ('tipus','=','export'),
            ('proces','=','D1'),
            ('pas','=', '02'),
            ('status', '=', 'correcte')
        ]
        swl_ids = swl_obj.search(cursor, uid, search_params)

        if len(swl_ids) > 0:
            swl = swl_obj.browse(cursor, uid, swl_ids[0])
            result['day'] = dateformat(swl.case_date)
        

        return result
