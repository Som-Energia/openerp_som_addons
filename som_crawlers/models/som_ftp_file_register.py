from osv import osv, fields


class SomFtpFileRegister(osv.osv):

    _name = "som.ftp.file.register"
    _order = "date_download desc"

    _columns = {
        "name": fields.char("File name", size=100, readonly=True),
        "date_download": fields.datetime("Date download", readonly=True),
        "date_imported": fields.datetime("Date imported to ERP"),
        "server_from": fields.char("Server", size=100, readonly=True),
        "state": fields.selection(
            [
                ("init", "Init"),
                ("downloaded", "Downloaded"),
                ("imported", "Imported"),
                ("error", "Error"),
            ],
            "State",
            readonly=True,
        ),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


SomFtpFileRegister()
