
from osv import osv, fields
from datetime import datetime, timedelta

class classeConfiguracio(osv.osv):
    _name = 'classe.configuracio'

    _columns = {
        'name' : fields.char('Nom', size=10, required=True,),
        'usuari' : fields.char('Usuari del portal', size=10,required=True, unique = True,),
        'contrasenya' : fields.char('Contrasenya del portal', size=15, required=True,),
        'url_portal' : fields.char('Url del portal', size=35, required=False,),
        'date_ultima_modificacio' : fields.datetime('Data i hora ultima modificacio',required=False,),
        'user_ultima_modificacio': fields.many2one(
            'res.users',
            string='Modificat per',
            help='Usuai qui ha realitzar la ultima modificacio de la contrasenya')
    }

    def canviar_contrasenya(self, cursor, uid, ids, contrasenya, context=None):        
     
        self.write(cursor,uid,ids,{'contrasenya': contrasenya , 'user_ultima_modificacio': uid, 'date_ultima_modificacio': datetime.now().isoformat()}, context=context)
        return 
        
        

classeConfiguracio()

class classeAccionsPlanificades(osv.osv):
    _name = 'classe.accions.planificades'

    _columns = {
        'name' : fields.char('Configuracio', size=10,required=True,),
        'data_execucio' : fields.date('Data execucio',required=False,),
        'data_ultima_execucio' : fields.date('Data ultima execucio', size=10,required=False,),
        'llista_execucions' : fields.char('Llista execucions que ha fet', size=10,required=False,),
    }

classeAccionsPlanificades()