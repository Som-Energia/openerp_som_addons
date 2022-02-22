class energy_prices:
    
    def get_data(self, cursor, uid, object, extra_text, context):

        if object.lang == 'es_ES':
            link = 'https://www.somenergia.coop/tarifa_indexada/ES_EiE_Explicacion_Tarifa_Indexada_Entidades_y_Empresas_Som_Energia.pdf'
        else:
            link = 'https://www.somenergia.coop/tarifa_indexada/CA_EiE_Explicacio_Tarifa_Indexada_Entitats_i_Empreses_Som_Energia.pdf'

        return {
            'k_plus_D': extra_text.get("marge", "ERROR EXTRA TEXT: sense marge"),
            'link': link,
            }