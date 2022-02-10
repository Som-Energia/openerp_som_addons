class energy_prices:
    
    def get_data(self, cursor, uid, object, extra_text, context):
        return {'k_plus_D': extra_text.get("marge", "ERROR EXTRA TEXT: sense marge")}
