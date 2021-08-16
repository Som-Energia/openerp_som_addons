from gestionatr.utils import get_description
from ..component_utils import dateformat
from ..ProcesC1 import ProcesC1

class C101(ProcesC1.ProcesC1):
    def __init__(self):
        ProcesC1.ProcesC1.__init__(self)

    def get_data(self, wiz, cursor, uid, step):
        result = ProcesC1.ProcesC1.get_data(self, wiz, cursor, uid, step)
        result['type'] = 'C101'
        result['text'] = step.comentaris
        if len(step.document_ids) == 0:
            result['adjunts'] = False

        swl_obj = step.pool.get('giscedata.switching.log')

        search_params = [
                        ('request_code','=',step.sw_id.codi_sollicitud),
                        ('tipus','=','export'),
                        ('proces','=','C1'),
                        ('pas','=', '01'),
                        ('status', '=', 'correcte')
        ]
        swl_ids = swl_obj.search(cursor, uid, search_params)
        if len(swl_ids) > 0:
            swl = swl_obj.browse(cursor, uid, swl_ids[0])
            result['day'] = dateformat(swl.case_date)

        return result