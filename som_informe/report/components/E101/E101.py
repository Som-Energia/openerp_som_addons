from gestionatr.utils import get_description
from ..ProcesE1 import ProcesE1

class E101(ProcesE1.ProcesE1):
    def __init__(self):
        ProcesE1.ProcesE1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesE1.ProcesE1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'E101'
        result['tipus_solicitud'] =  get_description(step.tipus_sollicitud, "TABLA_122")
        result['codi_subjacent'] =step.atr_subjacent.codi_sollicitud
        result['data_subjacent'] = step.atr_subjacent.data_sollicitud

        """"
        swl_obj = step.pool.get('giscedata.switching.log')

        search_params = [
            ('request_code','=',step.sw_id.codi_sollicitud),
            ('tipus','=','export'),
            ('proces','=','C2'),
            ('pas','=', '01'),
            ('status', '=', 'correcte')
        ]
        swl_ids = swl_obj.search(cursor, uid, search_params)

        if len(swl_ids) > 0:
            swl = swl_obj.browse(cursor, uid, swl_ids[0])
            result['day'] = dateformat(swl.case_date)
        """

        return result
