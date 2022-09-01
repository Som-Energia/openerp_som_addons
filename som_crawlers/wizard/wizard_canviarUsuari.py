## Describes the module(wizard) that modifies the old password for a new one
#imports
from osv import osv, fields
from tools.translate import _
# @author Ikram Ahdadouche El Idrissi
# @author Dalila Jbilou Kouhous
## Describes the module and contains the function that changes the password
class WizardCanviarUsuari(osv.osv_memory):

    ## Module name
    _name = 'wizard.canviarUsuari'

    ## Wizard function that changes the password of a configuration which id is activated
    # @param self The object pointer
    # @param cursor The database pointer
    # @param uid The current user
    # @param ids List of selected configuration
    # @param context None certain data to pass
    # @return ir.actions.act_window_close that closes the wizard window

    def canviar_usuari(self,cursor, uid, ids, context=None):

        if not context:
            return False

        ##Control ids
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        wiz = self.browse(cursor, uid, ids[0], context=context)
        usuari = wiz.usuari_nou

        active_ids = context.get('active_ids')
        ##Load the module
        classconf = self.pool.get('som.crawlers.config')
        for id in active_ids:
            classconf.canviar_usuari(cursor, uid, id, usuari, context=context)

        return {'type': 'ir.actions.act_window_close'}

    ##Column definition : usuari nou, the user puts the new user
    _columns = {
    'usuari_nou': fields.char("Usuari_nou", size = 30, required=True, help="Entra el nou usuari",)
    }
WizardCanviarUsuari()