from datetime import datetime


class first_page:
    def get_data(self, cursor, uid, object, extra_text, context):
        return {
            "lang": object.lang,
            "nom_titular": object.partner_id.name,
            "data_oferta": datetime.today().strftime("%d-%m-%Y"),
            "codi_oferta": extra_text.get("codi_oferta", "ERROR EXTRA TEXT: sense codi oferta"),
        }
