## Describes the module(wizard) that modifies the old password for a new one
#imports
from osv import osv, fields
from tools.translate import _
# @author Ikram Ahdadouche El Idrissi
# @author Dalila Jbilou Kouhous
## Describes the module and contains the function that changes the password
class WizardCanviarContrasenya(osv.osv_memory):

    ## Module name
    _name = 'wizard.canviarContrasenya'

    ## Wizard function that changes the password of a configuration which id is activated
        # @param self The object pointer
        # @param cursor The database pointer
        # @param uid The current user
        # @param ids List of selected configuration
        # @param context None certain data to pass
        # @return ir.actions.act_window_close that closes the wizard window

    def canviar_contrasenya(self,cursor, uid, ids, context=None):

        if not context:
            return False

        ##Control ids
        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        wiz = self.browse(cursor, uid, ids[0], context=context)
        contrasenya = wiz.contrasenya_nova

        active_ids = context.get('active_ids')
        ##Load the module
        classconf = self.pool.get('som.crawlers.config')
        for id in active_ids:
            classconf.canviar_contrasenya(cursor, uid, id, contrasenya, context=context)

        return {'type': 'ir.actions.act_window_close'}

    ##Column definition : contrasenya nova, the user puts the new password
    _columns = {
        'contrasenya_nova': fields.char("Contrasenya nova", size = 30, required=True, help="Entra la teva nova contrasenya",)
    }
WizardCanviarContrasenya()