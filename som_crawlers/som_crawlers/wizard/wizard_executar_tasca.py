from osv import osv, fields
from tools.translate import _
import os
from datetime import datetime

class WizardExecutarTasca(osv.osv_memory):
    _name= 'wizard.executar.tasca'

    def executar_tasca(self, cursor, uid, ids, context=None):

        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get('active_ids',[])
        wiz = self.browse(cursor, uid, ids[0], context=context)

        fitxer = wiz.nom_fitxer
        classtask = self.pool.get('som.crawlers.task')
        classresult = self.pool.get('som.crawlers.result')
        for id in active_ids:
            resultat = os.system("python3 " + fitxer)
            if resultat == 0:
                resultat = 'ok'
            else:
                resultat = 'Error'

            data_i_hora = datetime.now().isoformat()
            classresult.create(cursor,uid,{'task_id': id, 'data_i_hora_execucio': data_i_hora, 'resultat':resultat})

        return {'type': 'ir.actions.act_window_close'}

    _columns = {
    'nom_fitxer': fields.char("Nom fitxer", size = 256, required=True, help="Nom del fitxer que vols introduir en el ERP",),
    }

WizardExecutarTasca()