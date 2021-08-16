from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesC2 import ProcesC2

class C204(ProcesC2.ProcesC2):
    def __init__(self):
        ProcesC2.ProcesC2.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC2.ProcesC2.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'C204'
        result['data_rebuig'] = step.data_rebuig
        result['rebutjos'] = []
        for rebuig in step.rebuig_ids:
            result['rebutjos'].append({
                    'codi' : rebuig.motiu_rebuig.name,
                    'descripcio' : rebuig.desc_rebuig
                })

        """
        swl_obj = step.pool.get('giscedata.switching.log')

        search_params = [
            ('request_code','=',step.sw_id.codi_sollicitud),
            ('tipus','=','export'),
            ('proces','=','C2'),
            ('pas','=', '04'),
            ('status', '=', 'correcte')
        ]
        swl_ids = swl_obj.search(cursor, uid, search_params)

        if len(swl_ids) > 0:
            swl = swl_obj.browse(cursor, uid, swl_ids[0])
            result['day'] = dateformat(swl.case_date)
        """

        return result