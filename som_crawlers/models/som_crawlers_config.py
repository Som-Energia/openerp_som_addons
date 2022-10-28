# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime


class SomCrawlersConfig(osv.osv):

    _name = "som.crawlers.config"

    _columns = {
        "name": fields.char(
            "Nom",
            size=50,
            required=True,
        ),
        "usuari": fields.char(
            "Usuari del portal",
            size=20,
            unique=True,
            help="Usuari del portal web o servidor FTP/SFTP",
        ),
        "contrasenya": fields.char(
            "Contrasenya del portal",
            size=30,
            help="Contrasenya del portal web o servidor FTP/SFTP",
        ),
        "url_portal": fields.char(
            "URL del portal",
            size=300,
            required=False,
            help="URL del portal web o direcció del servidor FTP/SFTP",
        ),
        "url_upload": fields.char(
            "URL de càrrega del portal",
            size=300,
            required=False,
        ),
        "filtres": fields.text(
            "Filtres de descàrrega",
            required=False,
        ),
        "date_ultima_modificacio": fields.datetime(
            "Data i hora última modificació",
            required=False,
        ),
        "user_ultima_modificacio": fields.many2one(
            "res.users",
            string="Modificat per",
            help="Usuari que ha realitzat la última modificació de la contrasenya",
        ),
        "crawler": fields.char(
            "Crawler",
            size=20,
            required=False,
        ),
        "days_of_margin": fields.integer(
            "Dies de marge",
            required=True,
        ),
        "pending_files_only": fields.boolean(
            "Només fitxers pendents",
        ),
        "browser": fields.char(
            "Navegador",
            size=30,
            required=True,
        ),
        "distribuidora": fields.many2one(
            "res.partner",
            "Distribuïdora",
        ),
        "port": fields.integer("Port FTP/SFTP"),
        "ftp": fields.boolean("FTP", help="Utilitzar FTP en comptes de SFTP"),
    }
    """canvia la contrasenya d'un portal i retorna la nova contrasenya
        @param self The object pointer
        @param cursor The database pointer
        @param uid The current user
        @param ids The crawler configuration id
        @param contrasenya The new password
        @param context None certain data to pass
        @return New password value
    """
    # testo ok
    def canviar_contrasenya(self, cursor, uid, ids, contrasenya, context=None):

        crawler_config = self.browse(cursor, uid, ids, context=context)
        if contrasenya == crawler_config.contrasenya:
            raise osv.except_osv(
                "Contrasenya identica a la anterior!",
                "Torna a introduir una contrasenya diferent a la anterior",
            )
        else:
            self.write(
                cursor,
                uid,
                ids,
                {
                    "contrasenya": contrasenya,
                    "user_ultima_modificacio": uid,
                    "date_ultima_modificacio": datetime.now().isoformat(),
                },
                context=context,
            )
            return contrasenya

    """canvia el nom d'usuari d'un portal i retorna el nou usuari
        @param self The object pointer
        @param cursor The database pointer
        @param uid The current user
        @param ids The crawler configuration id
        @param usuari The new user
        @param context None certain data to pass
        @return New user value
    """

    def canviar_usuari(self, cursor, uid, ids, usuari, context=None):

        crawler_config = self.browse(cursor, uid, ids, context=context)
        if usuari == crawler_config.usuari:
            raise osv.except_osv(
                "Usuari identic a l'anterior!",
                "Torna a introduir un usuari diferent a l'anterior",
            )
        else:
            self.write(
                cursor,
                uid,
                ids,
                {
                    "usuari": usuari,
                    "user_ultima_modificacio": uid,
                    "date_ultima_modificacio": datetime.now().isoformat(),
                },
                context=context,
            )
            return usuari

    def canviar_dies_de_marge(self, cursor, uid, ids, days, context=None):

        crawler_config = self.browse(cursor, uid, ids, context=context)
        if days == crawler_config.days_of_margin:
            raise osv.except_osv(
                "Nombre de dies igual a l'anterior!",
                "Introdueix un nombre diferent mes gran o igual a 0",
            )
        elif days < 0:
            raise osv.except_osv(
                "Nombre negatiu!", "Introdueix un nombre mes gran o igual a 0 diferent"
            )
        else:
            self.write(
                cursor,
                uid,
                ids,
                {
                    "days_of_margin": days,
                    "user_ultima_modificacio": uid,
                    "date_ultima_modificacio": datetime.now().isoformat(),
                },
                context=context,
            )
            return days


SomCrawlersConfig()
