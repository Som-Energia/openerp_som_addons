
from osv import osv, fields
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class SomCrawlersConfig(osv.osv):
    _name = 'som.crawlers.config'

    _columns = {
        'name': fields.char('Nom', size=10, required=True,),
        'usuari' : fields.char('Usuari del portal', size=10,required=True, unique = True,),
        'contrasenya' : fields.char('Contrasenya del portal', size=15, required=True,),
        'url_portal' : fields.char('Url del portal', size=200, required=False,),
        'filtres' : fields.char('Filtres de descarrega', size=200, required=False,),
        'date_ultima_modificacio' : fields.datetime('Data i hora ultima modificacio',required=False,),
        'user_ultima_modificacio': fields.many2one(
            'res.users',
            string='Modificat per',
            help='Usuari que ha realitzat la ultima modificacio de la contrasenya'),
        'crawler' : fields.char('Crawler', size = 20, required = False,),
        'days_of_margin' : fields.integer('Dies de marge', required = True,),
        'pending_files_only': fields.boolean('Nomes fitxers pendents',),
        'browser': fields.char('Navegador', size=30, required=True,),
    }

    def canviar_contrasenya(self, cursor, uid, ids, contrasenya, context=None):
        crawler_config = self.browse(cursor,uid,ids,context=context)
        if contrasenya == crawler_config.contrasenya:
            raise osv.except_osv('Contrasenya identica a la anterior!','Torna a introduir una contrasenya diferent a la anterior')
        else:
            #key = Fernet.generate_key()
            #fernet = Fernet(key)
            #enctex = fernet.encrypt(contrasenya.encode())
            self.write(cursor,uid,ids,{'contrasenya': contrasenya, 'user_ultima_modificacio': uid, 'date_ultima_modificacio': datetime.now().isoformat()}, context=context)
            return contrasenya

SomCrawlersConfig()



