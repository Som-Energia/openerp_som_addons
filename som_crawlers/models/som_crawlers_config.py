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
            size=100,
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
            "Distribuidora",
            help="Distribuidora",
        ),
        "port": fields.integer("Port FTP/SFTP"),
        "ftp": fields.boolean("FTP", help="Utilitzar FTP en comptes de SFTP"),
        "log": fields.text(
            "Història",
            help="Història de modificacions de la configuració",
        ),
    }

    def _log(self, cursor, uid, ids, message):
        user_obj = self.pool.get("res.users")
        username = user_obj.browse(cursor, uid, uid, context=None).name

        if not isinstance(ids, list):
            ids = [ids]

        for id in ids:
            old_log = self.read(cursor, uid, id, ["log"], context=None)["log"]
            if not old_log:
                old_log = ""

            log = (
                "[{update_date} {user}] ".format(
                    update_date=datetime.now(),
                    user=username,
                )
                + message
                + "\n"
                + old_log
            )

            self.write(
                cursor,
                uid,
                id,
                {
                    "log": log,
                },
                context=None,
            )

    """canvia la contrasenya d'un portal i retorna la nova contrasenya
        @param self The object pointer
        @param cursor The database pointer
        @param uid The current user
        @param ids The crawler configuration id
        @param contrasenya The new password
        @param context None certain data to pass
        @return New password value
    """

    def canviar_contrasenya(self, cursor, uid, ids, contrasenya, context=None):
        contrasenya_antiga = self.browse(cursor, uid, ids, context=context).contrasenya

        if not contrasenya_antiga:
            contrasenya_antiga = ""

        if contrasenya == contrasenya_antiga:
            raise osv.except_osv(
                "Contrasenya identica a la anterior!",
                "Torna a introduir una contrasenya diferent a la anterior",
            )
        else:
            self.write(cursor, uid, ids, {"contrasenya": contrasenya}, context=None)
            message = ("S'ha actualitzat la contrasenya")
            self._log(cursor, uid, ids, message)

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
        usuari_antic = self.browse(cursor, uid, ids, context=context).usuari

        if not usuari_antic:
            usuari_antic = ""

        if usuari == usuari_antic:
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
                },
                context=None,
            )
            message = (
                "S'ha actualitzat l'usuari: \"" + str(usuari_antic) + '" -> "' + str(usuari) + '"'
            )
            self._log(cursor, uid, ids, message)

            return usuari

    def canviar_dies_de_marge(self, cursor, uid, ids, days, context=None):
        days_old = self.browse(cursor, uid, ids, context=context).days_of_margin

        if not days_old:
            days_old = 0

        if days == days_old:
            raise osv.except_osv(
                "Nombre de dies igual a l'anterior!",
                "Introdueix un nombre diferent mes gran o igual a 0",
            )
        elif days < 0:
            raise osv.except_osv(
                "Nombre negatiu!", "Introdueix un nombre mes gran o igual a 0 diferent"
            )
        else:
            self.write(cursor, uid, ids, {"days_of_margin": days}, context=None)
            message = "S'ha actualitzat els dies de marge: " + str(days_old) + " -> " + str(days)
            self._log(cursor, uid, ids, message)

            return days

    def change_field_value(
        self, cursor, uid, ids, field_name, field_label, new_value, is_numeric=False, context=None
    ):
        old_value = self.browse(cursor, uid, ids, context=context).read()[0][field_name]

        if not old_value:
            old_value = "" if not is_numeric else 0

        if new_value == old_value:
            raise osv.except_osv(
                "El nou valor és identic a l'anterior!",
                "Torna a introduir una valor diferent a la anterior",
            )
        else:
            self.write(cursor, uid, ids, {field_name: new_value}, context=None)
            message = (
                "S'ha actualitzat el valor: "
                + field_label
                + ': "'
                + str(old_value)
                + '" -> "'
                + str(new_value)
                + '"'
            )
            self._log(cursor, uid, ids, message)

            return new_value


SomCrawlersConfig()
