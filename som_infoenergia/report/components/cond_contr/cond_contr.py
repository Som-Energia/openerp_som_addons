class cond_contr:
    def get_data(self, cursor, uid, object, extra_text, context):
        if object.lang == "es_ES":
            return {
                "link": "https://es.support.somenergia.coop/article/144-cuales-son-las-ventajas-de-ser-socio-a-de-som-energia"
            }
        else:
            return {
                "link": "https://ca.support.somenergia.coop/article/186-quins-son-els-avantatges-de-ser-soci-a-de-som-energia"
            }
