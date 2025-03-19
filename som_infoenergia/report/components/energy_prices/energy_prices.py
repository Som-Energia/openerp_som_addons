class energy_prices:
    def get_data(self, cursor, uid, object, extra_text, context):

        if object.lang == "es_ES":
            link = "https://www.somenergia.coop/documentacio_EiE/ES_EiE_Explica_Tarifa%20Indexada%20para%20Entidades%20y%20Empresas_Som%20Energia.pdf"  # noqa: E501

        else:
            link = "https://www.somenergia.coop/documentacio_EiE/CA_EiE_Explica_Tarifa%20Indexada%20per%20Entitats%20i%20Empreses_Som%20Energia.pdf"  # noqa: E501

        return {
            "k_plus_D": extra_text.get("marge", "ERROR EXTRA TEXT: sense marge"),
            "link": link,
        }
