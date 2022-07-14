from osv import osv, fields
from tools.translate import _

class WizardCanviarContrasenya(osv.osv_memory):
    _name = 'wizard.canviarContrasenya'

    def canviar_contrasenya(self,cursor, uid, ids, context=None):
        if not context:
            return False

        #Controlar tema ids[]
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        wiz = self.browse(cursor, uid, ids[0], context=context)
        contrasenya = wiz.contrasenya_nova

        active_id = context.get('active_id')
        active_ids = context.get('active_ids')
        import pudb;pu.db
        #carregar el model
        classconf = self.pool.get('classe.configuracio')

        #cridar el passar revisio
        for id in active_ids:
            classconf.canviar_contrasenya(cursor, uid, id, contrasenya, context=context)

        return {'type': 'ir.actions.act_window_close'}
    
    _columns = {
        'contrasenya_nova': fields.char("Contrasenya nova", size = 30, required=True, help="Entra la teva nova contrasenya",)
    }
WizardCanviarContrasenya()